"""Plan overlay: a list of operations drafted on top of a Jira snapshot. Pure: no network, no Jira client, never writes to Jira.

A plan is {name, base: {project, fetched}, ops: [...]}. Operations (all keys below are required unless noted):
  add_slice    {slice: {id?, epic, title, kind, mode, days, value_share, unblocks, releasable, learn, debt}}
  defer_epic   {epic}                       marks the epic deferred
  set_dates    {epic, start?, end?}         later ops override earlier ones key by key
  add_link     {from, to}                   `from` blocks `to`
  remove_link  {from, to}
`issues` is the po_view issue dict ({key: info}). apply() never mutates its inputs.
"""
import copy, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topology

CLOSED = {"Done", "Discarded", "Closed", "Cancelled", "Resolved"}
DEFAULT_SLICE_CAP_DAYS = 10
OP_ORDER = ("add_slice", "defer_epic", "set_dates", "add_link", "remove_link")
LINK_OPS = ("add_link", "remove_link")


def load_plan(path):
    return topology.load_config(path)


def _sort_key(op):
    kind = op["op"]
    if kind not in OP_ORDER:
        raise ValueError(f"unknown plan operation: {kind!r}")
    if kind == "add_slice":
        return 0, op["slice"].get("id") or "", ""
    if kind in LINK_OPS:  # one rank for both, so add/remove of the same link keep their written order
        return 3, op["from"], op["to"]
    return OP_ORDER.index(kind), op["epic"], ""


def dump_plan(plan, path=None):
    """JSON with sorted keys and ops in canonical order (stable sort), so a git diff shows only real changes."""
    plan = dict(plan, ops=sorted(plan.get("ops", []), key=_sort_key))
    text = json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        with open(os.path.expanduser(path), "w") as f:
            f.write(text)
    return text


def slices(plan):
    """The plan's slices as dicts, in op order. A slice without an id gets a temporary 'S-<n>' (n = its position)."""
    out = []
    for op in plan.get("ops", []):
        if op["op"] == "add_slice":
            s = copy.deepcopy(op["slice"])
            s.setdefault("id", f"S-{len(out) + 1}")
            out.append(s)
    return out


def _ref(issue):
    return dict(k=issue["key"], st=issue["st"], s=issue["sum"], ext=False)


def _link(issues, a, b):
    if all(r["k"] != b for r in issues[a]["blocks"]):
        issues[a]["blocks"].append(_ref(issues[b]))
    if all(r["k"] != a for r in issues[b]["blockedBy"]):
        issues[b]["blockedBy"].append(_ref(issues[a]))


def _unlink(issues, a, b):
    issues[a]["blocks"] = [r for r in issues[a]["blocks"] if r["k"] != b]
    issues[b]["blockedBy"] = [r for r in issues[b]["blockedBy"] if r["k"] != a]


def _slice_issue(s):
    return dict(key=s["id"], sum=s["title"], st="Planned", pr="", ws=None, who="", team="", par=s["epic"], start=None, end=None,
                url="", core=False, blocks=[], blockedBy=[], relates=[], labels=[], due=None, refine="", flagged=False,
                slice=copy.deepcopy(s))


def _problem(issues, key):
    if key not in issues:
        return "missing"
    if issues[key]["st"] in CLOSED:
        return "closed"


def apply(issues, plan):
    """Return (new_issues, report). report = {applied: [op index], conflicts: [{op, index, epic, reason}], slices: [ids]}.
    An op that touches an epic missing or closed in the snapshot is a conflict and is skipped; the rest applies."""
    out = copy.deepcopy(issues)
    report = dict(applied=[], conflicts=[], slices=[])
    conflict = lambda i, op, key, why: report["conflicts"].append(dict(op=op["op"], index=i, epic=key, reason=why))
    ops = plan.get("ops", [])
    pending = []  # (slice issue) whose unblocks are wired once every slice exists
    for i, op in enumerate(ops):
        kind = op["op"]
        if kind not in OP_ORDER:
            raise ValueError(f"unknown plan operation: {kind!r}")
        touched = [op["slice"]["epic"]] if kind == "add_slice" else [op["from"], op["to"]] if kind in LINK_OPS else [op["epic"]]
        bad = [(k, _problem(out, k)) for k in touched if _problem(out, k)]
        if bad:
            for k, why in bad:
                conflict(i, op, k, why)
            continue
        report["applied"].append(i)
        if kind == "add_slice":
            s = dict(op["slice"], id=op["slice"].get("id") or f"S-{sum(1 for o in ops[:i + 1] if o['op'] == 'add_slice')}")
            out[s["id"]] = _slice_issue(s)
            pending.append(out[s["id"]])
            report["slices"].append(s["id"])
        elif kind == "defer_epic":
            out[op["epic"]]["deferred"] = True
        elif kind == "set_dates":
            for f in ("start", "end"):
                if f in op:
                    out[op["epic"]][f] = op[f]
        elif kind == "add_link":
            _link(out, op["from"], op["to"])
        else:
            _unlink(out, op["from"], op["to"])
    for issue in pending:
        for target in issue["slice"].get("unblocks", []):
            why = _problem(out, target)
            if why:
                conflict(None, dict(op="add_slice"), target, why)
            else:
                _link(out, issue["key"], target)
    return out, report


def _cap(epic_key, cfg):
    kind, pod = topology.classify(epic_key, cfg or {})
    default = DEFAULT_SLICE_CAP_DAYS
    return ((cfg or {}).get("policy") or {}).get(pod, {}).get("slice_cap_days", default) if kind == "pod" else default


def validate(plan, issues, cfg=None):
    """Findings as dicts {rule, message, slice|epic}. Rules: split-me, unrepaid-debt, value-share-over, unknown-unblocks."""
    found = []
    all_slices = slices(plan)
    ids = {s["id"] for s in all_slices}
    shares = {}
    for s in all_slices:
        cap = _cap(s["epic"], cfg)
        if s["days"] > cap:
            found.append(dict(rule="split-me", slice=s["id"], message=f"{s['id']} is {s['days']} days, over the {cap}-day cap: split me"))
        debt = s.get("debt")
        if s.get("mode") == "manual" and debt:
            repaid = debt.get("repaid_by")
            if not repaid or repaid == s["id"] or repaid not in ids:
                found.append(dict(rule="unrepaid-debt", slice=s["id"],
                                  message=f"{s['id']} is manual and creates debt ({debt.get('creates', '')}) with no later slice that repays it"))
        shares[s["epic"]] = shares.get(s["epic"], 0) + (s.get("value_share") or 0)
        for target in s.get("unblocks", []):
            if target not in ids and target not in issues:
                found.append(dict(rule="unknown-unblocks", slice=s["id"], message=f"{s['id']} unblocks {target}, which is not in the plan or snapshot"))
    for epic_key, total in sorted(shares.items()):
        if total > 1.0 + 1e-9:
            found.append(dict(rule="value-share-over", epic=epic_key, message=f"value shares of {epic_key} total {total:g}, over 1.0"))
    return found


def time_to_first_releasable(plan, epic):
    """Days until the first releasable slice of `epic` ships: its own days plus the days of every slice that must come first
    (slices of the epic that unblock it, directly or not), worked one after another. None if no slice is releasable."""
    mine = {s["id"]: s for s in slices(plan) if s["epic"] == epic}
    before = {k: set() for k in mine}
    for s in mine.values():
        for t in s.get("unblocks", []):
            if t in before:
                before[t].add(s["id"])

    def needed(k, seen):
        for p in before[k]:
            if p not in seen:
                seen.add(p)
                needed(p, seen)
        return seen
    times = [mine[k]["days"] + sum(mine[p]["days"] for p in needed(k, set()) - {k}) for k in mine if mine[k].get("releasable")]
    return min(times) if times else None


def _link_state(plan):
    state = {}
    for op in plan.get("ops", []):
        if op["op"] in LINK_OPS:
            state[(op["from"], op["to"])] = "add" if op["op"] == "add_link" else "remove"
    return state


def _date_state(plan):
    state = {}
    for op in plan.get("ops", []):
        if op["op"] == "set_dates":
            cur = state.setdefault(op["epic"], dict(start=None, end=None))
            cur.update({f: op[f] for f in ("start", "end") if f in op})
    return state


def diff(plan_a, plan_b):
    """What changes going from plan_a to plan_b: slices added/removed/changed, links (add/remove/none), dates, deferred epics."""
    sa, sb = {s["id"]: s for s in slices(plan_a)}, {s["id"]: s for s in slices(plan_b)}
    changed = []
    for k in sorted(sa.keys() & sb.keys()):
        f = {n: [sa[k].get(n), sb[k].get(n)] for n in sorted(sa[k].keys() | sb[k].keys()) if sa[k].get(n) != sb[k].get(n)}
        if f:
            changed.append(dict(id=k, fields=f))
    la, lb = _link_state(plan_a), _link_state(plan_b)
    links = [dict({"from": a, "to": b}, a=la.get((a, b), "none"), b=lb.get((a, b), "none"))
             for a, b in sorted(la.keys() | lb.keys()) if la.get((a, b)) != lb.get((a, b))]
    da, db = _date_state(plan_a), _date_state(plan_b)
    blank = dict(start=None, end=None)
    dates = [dict(epic=e, a=da.get(e, blank), b=db.get(e, blank)) for e in sorted(da.keys() | db.keys()) if da.get(e, blank) != db.get(e, blank)]
    xa = {o["epic"] for o in plan_a.get("ops", []) if o["op"] == "defer_epic"}
    xb = {o["epic"] for o in plan_b.get("ops", []) if o["op"] == "defer_epic"}
    deferred = [dict(epic=e, a=e in xa, b=e in xb) for e in sorted(xa ^ xb)]
    return dict(slices_added=sorted(sb.keys() - sa.keys()), slices_removed=sorted(sa.keys() - sb.keys()), slices_changed=changed,
                links=links, dates=dates, deferred=deferred)
