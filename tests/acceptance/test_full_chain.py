import subprocess


def test_full_chain():
    """
    Note that this test is excluded from coverage because coverage should be
    for unit tests.
    """

    result = subprocess.run(
        ["raincoat", "tests/acceptance/test_project", "--exclude=*ignored*"],
        stdout=subprocess.PIPE,
    )
    output = result.stdout.decode("utf-8").strip()
    print(output)
    assert result.returncode != 0

    expected = """
Django ticket #25981 (from tests/acceptance/test_project/__init__.py:13)
Ticket #25981 has been merged in Django 4.1.2

ewjoachim/umbrella@1.0.0 vs master branch (95f492efa41d51d47c469e00c28c063256faa56c) at umbrella/__init__.py:main (from tests/acceptance/test_project/__init__.py:15)
Code is different:
--- umbrella/__init__.py
+++ umbrella/__init__.py
@@ -2,5 +2,5 @@
try:
curses.wrapper(loop)
except ScreenTooSmall:
-        print("Screen too small")
+        print("Screen is too small")
sys.exit(1)

raincoat_umbrella == 1.0.0 vs 2.0.0 @ umbrella/__init__.py:main (from tests/acceptance/test_project/__init__.py:7)
Code is different:
--- umbrella/__init__.py
+++ umbrella/__init__.py
@@ -2,5 +2,5 @@
try:
curses.wrapper(loop)
except ScreenTooSmall:
-        print("Screen too small")
+        print("Screen is too small")
sys.exit(1)

raincoat_umbrella == 1.0.0 vs 2.0.0 @ umbrella/__init__.py:Drop.fall (from tests/acceptance/test_project/__init__.py:8)
Code is different:
--- umbrella/__init__.py
+++ umbrella/__init__.py
@@ -6,6 +6,6 @@
char = chr(self.window.inch(self.y, self.x) & (2 ** 8 - 1))
if char != " ":
raise self.FellOnSomething
-            self.draw(self.char)
+            self.draw(char=self.char)
except curses.error:
raise self.FellOnSomething

raincoat_umbrella == 1.0.0 vs 2.0.0 @ umbrella/__init__.py:Drop (from tests/acceptance/test_project/__init__.py:9)
Code is different:
--- umbrella/__init__.py
+++ umbrella/__init__.py
@@ -23,6 +23,6 @@
char = chr(self.window.inch(self.y, self.x) & (2 ** 8 - 1))
if char != " ":
raise self.FellOnSomething
-            self.draw(self.char)
+            self.draw(char=self.char)
except curses.error:
raise self.FellOnSomething

raincoat_umbrella == 1.0.0 vs 2.0.0 @ umbrella/__init__.py:whole module (from tests/acceptance/test_project/__init__.py:10)
Code is different:
--- umbrella/__init__.py
+++ umbrella/__init__.py
@@ -62,7 +62,7 @@
char = chr(self.window.inch(self.y, self.x) & (2 ** 8 - 1))
if char != " ":
raise self.FellOnSomething
-            self.draw(self.char)
+            self.draw(char=self.char)
except curses.error:
raise self.FellOnSomething
@@ -111,7 +111,7 @@
try:
curses.wrapper(loop)
except ScreenTooSmall:
-        print("Screen too small")
+        print("Screen is too small")
sys.exit(1)
@@ -168,7 +168,7 @@
if width < MIN_SIZE[0] or height < MIN_SIZE[1]:
raise ScreenTooSmall
-        if len(drops) < height * height * DROPS_RATIO:
+        if len(drops) < height * width * DROPS_RATIO:
drops.add(Drop(window))
for drop in list(drops):

raincoat_umbrella == 1.0.0 vs 2.0.0 @ umbrella/__init__.py:non_existant (from tests/acceptance/test_project/__init__.py:11)
Invalid Raincoat PyPI comment : non_existant does not exist in umbrella/__init__.py

raincoat_umbrella == 1.0.0 vs 2.0.0 @ umbrella/non_existant.py:whole module (from tests/acceptance/test_project/__init__.py:12)
Invalid Raincoat PyPI comment : umbrella/non_existant.py does not exist""".strip()

    # It's ok if the output has lines that we don't have,
    # but all the expected lines should be there.
    for line in expected.splitlines():
        assert line in output
