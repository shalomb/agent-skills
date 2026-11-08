import importlib.util, os, tempfile, unittest

HERE = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location("urls", os.path.join(HERE, "..", "scripts", "urls.py"))
urls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(urls)


class RelUnderRoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.root, "teach", "x", "lessons"))
        self.f = os.path.join(self.root, "teach", "x", "lessons", "a.html")
        open(self.f, "w").write("x")

    def tearDown(self):
        self.tmp.cleanup()

    def test_file_under_root_gives_relative_path(self):
        self.assertEqual(urls.rel_under_root(self.f, self.root), "teach/x/lessons/a.html")

    def test_outside_root_refused(self):
        self.assertIsNone(urls.rel_under_root("/etc/hostname", self.root))

    def test_dot_segment_refused(self):
        d = os.path.join(self.root, ".hidden"); os.makedirs(d)
        p = os.path.join(d, "a.html"); open(p, "w").write("x")
        self.assertIsNone(urls.rel_under_root(p, self.root))

    def test_symlink_refused(self):
        link = os.path.join(self.root, "teach", "link.html")
        os.symlink(self.f, link)
        self.assertIsNone(urls.rel_under_root(link, self.root))

    def test_symlinked_directory_in_path_refused(self):
        os.symlink(os.path.join(self.root, "teach", "x"), os.path.join(self.root, "teach", "dirlink"))
        via = os.path.join(self.root, "teach", "dirlink", "lessons", "a.html")
        self.assertIsNone(urls.rel_under_root(via, self.root))

    def test_missing_path_refused(self):
        self.assertIsNone(urls.rel_under_root(os.path.join(self.root, "nope"), self.root))


class BuildUrls(unittest.TestCase):
    def test_one_url_per_network_in_order(self):
        eps = [("parallels", "10.0.0.3", "8787"), ("tailnet", "100.1.1.1", "8787")]
        self.assertEqual(urls.build("teach/x/a.html", eps),
                         [("parallels", "http://10.0.0.3:8787/r/teach/x/a.html"),
                          ("tailnet", "http://100.1.1.1:8787/r/teach/x/a.html")])

    def test_directory_url_ends_with_slash(self):
        eps = [("parallels", "10.0.0.3", "8787")]
        self.assertTrue(urls.build("teach/x/", eps)[0][1].endswith("/r/teach/x/"))

    def test_ipv6_host_is_bracketed(self):
        eps = [("tailnet", "fd7a::1", "8787")]
        self.assertIn("http://[fd7a::1]:8787/", urls.build("a", eps)[0][1])


class PortOmission(unittest.TestCase):
    def test_port_80_is_left_out_of_the_url(self):
        self.assertEqual(urls.build("teach/x/", [("url", "idun", "80")]), [("url", "http://idun/r/teach/x/")])

    def test_other_ports_are_kept(self):
        self.assertEqual(urls.build("a", [("url", "idun", "8787")]), [("url", "http://idun:8787/r/a")])


class SystemEndpoint(unittest.TestCase):
    def write(self, text):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d))
        path = os.path.join(d, "agent-skills.conf")
        open(path, "w").write(text)
        return path

    def test_reads_the_port_and_names_the_host_once(self):
        conf = self.write("server {\n  listen 80 default_server;\n  location /r/ { }\n}\n")
        self.assertEqual(urls.system_endpoint(conf, host="idun", probe=lambda port: True), [("url", "idun", "80")])

    def test_missing_conf_means_no_system_server(self):
        self.assertEqual(urls.system_endpoint("/nonexistent/x.conf", host="idun", probe=lambda p: True), [])

    def test_conf_without_the_report_location_is_not_ours(self):
        conf = self.write("server {\n  listen 80 default_server;\n}\n")
        self.assertEqual(urls.system_endpoint(conf, host="idun", probe=lambda p: True), [])

    def test_a_conf_whose_server_is_not_answering_is_not_used(self):
        conf = self.write("server {\n  listen 80 default_server;\n  location /r/ { }\n}\n")
        self.assertEqual(urls.system_endpoint(conf, host="idun", probe=lambda p: False), [])


if __name__ == "__main__":
    unittest.main()
