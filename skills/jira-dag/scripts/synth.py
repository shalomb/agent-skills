"""Synthetic portfolio for trying the page without Jira. Generic names only; dates are relative to today.

Deliberately mixed: one committed epic, some slipping behind blockers, an unowned epic, an unsliced epic,
an external blocker still in Backlog, a flagged impediment, an undated epic and an orphan. Nothing is real.
"""
import datetime as dt
from jira_common import finalize

P = "PLT"
BASE = "https://jira.example.invalid"
NAMES = {"APP": "Legacy Apps ART", "OPS": "Operations Enablement", "SEC": "Security Engineering", "NET": "Network Services", "PLT": "Platform"}


def monday():
    t = dt.date.today()
    return t - dt.timedelta(days=t.weekday())


def build():
    m = monday()
    W = lambda n: (m + dt.timedelta(weeks=n)).isoformat()
    inits = {"INIT-1": ("Customers onboard themselves in minutes", W(22)), "INIT-2": ("Platform stays up through a regional failure", W(18))}
    #        key,  summary,                                             status,        ws,  who,  start,end, due,  refine,    kids, par,     flag
    E = [("PLT-10", "A new customer signs up and gets a working account", "Implementing", 17.7, "Ana", 0, 10, 12, "Ready", 4, "INIT-1", False),
         ("PLT-11", "Every service logs to one searchable place", "Backlog", 9.2, "Ben", 1, 9, None, "Refine", 2, "INIT-1", False),
         ("PLT-12", "Payments are retried safely when a provider fails", "Funnel", 8.0, "Chi", 0, 4, None, "Refine", 0, "INIT-1", False),
         ("PLT-13", "Support sees the whole customer journey in one view", "Backlog", 6.5, "", 4, 14, None, "Refine", 1, "INIT-1", False),
         ("PLT-14", "Customers can invite their team", "Funnel", 5.0, "Dee", 8, 16, None, "Evaluate", 0, "INIT-1", False),
         ("PLT-15", "Services fail over to a second region", "Analyzing", 12.0, "Eli", 0, 12, None, "Refine", 1, "INIT-2", False),
         ("PLT-16", "Databases recover within an agreed time", "Backlog", 8.4, "Fay", 2, 12, None, "Refine", 3, "INIT-2", True),
         ("PLT-17", "The team is paged only for real incidents", "Funnel", 4.1, "Gus", 3, 9, None, "Refine", 2, "INIT-2", False),
         ("PLT-18", "Secrets are rotated without downtime", "Backlog", 5.6, "Hal", 0, 6, 7, "Ready", 1, "INIT-2", False),
         ("PLT-19", "Dashboards show cost per customer", "Funnel", 2.8, "Ivy", None, None, None, "Evaluate", 0, "INIT-1", False),
         ("PLT-20", "Old batch jobs are retired", "Funnel", 2.2, "Jon", 6, 12, None, "Evaluate", 0, None, False)]
    I = {}
    for k, s, st, ws, who, a, b, due, rf, kids, par, flag in E:
        I[k] = dict(key=k, sum=s, st=st, pr="Medium", ws=ws, who=who, team="Platform", par=par or "", start=W(a) if a is not None else None,
                    end=W(b) if b is not None else None, url=f"{BASE}/browse/{k}", core=True, blocks=[], blockedBy=[], relates=[],
                    due=W(due) if due else None, refine=rf, flagged=flag, children=kids, parsum=inits[par][0] if par else "",
                    pardue=inits[par][1] if par else None)
    labels = {"PLT-10": ["pi-demo", "area-onboarding"], "PLT-11": ["pi-demo", "area-observability"], "PLT-12": ["pi-demo", "area-payments"], "PLT-13": ["pi-demo", "area-support"],
              "PLT-14": ["pi-demo", "area-onboarding"], "PLT-15": ["pi-demo", "area-resilience"], "PLT-16": ["pi-demo", "area-resilience"], "PLT-17": ["pi-demo", "area-observability"],
              "PLT-18": ["pi-demo", "area-security"]}
    for k, l in labels.items():
        I[k]["labels"] = l
    X = {"SEC-3": ("Security review of the new sign-up flow", "Backlog", W(6)), "NET-7": ("Open the private link to the second region", "Backlog", None),
         "PLT-90": ("Create the shared build pipeline", "In Progress", W(5)), "PLT-91": ("Order the managed queue service", "Backlog", W(3)),
         "APP-5": ("Legacy billing app moves onto the platform", "Backlog", W(11)), "APP-8": ("Legacy reports read from the new logs", "Funnel", W(9)),
         "APP-9": ("Legacy checkout survives a region failure", "Funnel", W(20)), "OPS-4": ("Operations handover uses the new paging", "Backlog", W(10))}
    for k, (s, st, due) in X.items():
        I[k] = dict(key=k, sum=s, st=st, pr="", ws=None, who="", team="", par="", start=None, end=None, url=f"{BASE}/browse/{k}", core=False,
                    blocks=[], blockedBy=[], relates=[], due=due, refine="", flagged=False, children=None, parsum="", pardue=None)
    edges = [("PLT-90", "PLT-10"), ("PLT-10", "PLT-13"), ("PLT-10", "PLT-14"), ("PLT-11", "PLT-13"), ("PLT-11", "PLT-17"), ("PLT-12", "PLT-10"),
             ("PLT-15", "PLT-16"), ("PLT-18", "PLT-15"), ("SEC-3", "PLT-10"), ("NET-7", "PLT-15"), ("PLT-91", "PLT-12"), ("PLT-16", "PLT-17"),
             ("PLT-10", "APP-5"), ("PLT-18", "APP-5"), ("PLT-11", "APP-8"), ("PLT-15", "APP-9"), ("PLT-17", "OPS-4")]
    for a, b in edges:
        ref = lambda k: dict(k=k, st=I[k]["st"], s=I[k]["sum"], ext=k.split("-")[0] != P)
        I[a]["blocks"].append(ref(b))
        I[b]["blockedBy"].append(ref(a))
    for v in I.values():
        v.setdefault("labels", [])
    return finalize(I, P)


def flow():
    """Story-level flow data for the Pressure tab (same shape as pressure.from_jira)."""
    I = build()
    W = lambda n: (monday() + dt.timedelta(weeks=n)).isoformat()
    age = {"PLT-10": 6, "PLT-11": 3, "PLT-12": 25, "PLT-13": 18, "PLT-14": 9, "PLT-15": 12, "PLT-16": 34, "PLT-17": 5, "PLT-18": 7, "PLT-19": 40, "PLT-20": 22,
           "PLT-90": 5, "PLT-91": 21, "SEC-3": 15, "NET-7": 30, "APP-5": 8, "APP-8": 8, "APP-9": 8, "OPS-4": 8}
    alpha = {"PLT-10", "PLT-11", "PLT-12", "PLT-13", "PLT-14", "PLT-19", "PLT-20", "PLT-90"}
    N = {}
    for k, v in I.items():
        ext = k.split("-")[0] != P
        N[k] = dict(key=k, sum=v["sum"], st=v["st"], type="Epic" if v["core"] else ("Task" if not ext else "Story"), who=v["who"], due=v["due"],
                    age=age.get(k), team="" if ext else ("Pod Alpha" if k in alpha else "Pod Beta"), blocks=[r["k"] for r in v["blocks"]], ext=ext)
    N["PLT-91"]["due"] = W(1)
    N["NET-7"]["due"] = W(-1)
    N["PLT-90"]["who"] = "Ana"
    stories = [("PLT-31", "Define the account model", "Backlog", "", 16, "PLT-10", "Pod Alpha"), ("PLT-32", "Ship the log pipeline", "In Progress", "Ben", 3, "PLT-11", "Pod Alpha"),
               ("PLT-33", "Choose the failover pattern", "Backlog", "", 21, "PLT-15", "Pod Beta"), ("PLT-34", "Restore drill for the main database", "In Progress", "Fay", 31, "PLT-16", "Pod Beta"),
               ("PLT-35", "Agree the alert routing", "Backlog", "", 12, "PLT-17", "Pod Beta")]
    for k, s, st, who, a, blocks, team in stories:
        N[k] = dict(key=k, sum=s, st=st, type="Story", who=who, due=None, age=a, team=team, blocks=[blocks], ext=False)
    N["PLT-31"]["blocks"].append("PLT-90")
    return N
