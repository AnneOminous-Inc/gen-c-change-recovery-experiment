# Explain, check, and recover one change

This is a fictional local project: a word counter. Its entire application is
`counter.py`. It reads the text you type, prints a count, and does not write files.
It uses Python's standard library; it needs no account, agent, network, or extra
package. The scripted exercise deliberately breaks this copy of the project.
That mistake is synthetic practice, not a proposed improvement for a real app.

## What the app promises

A "word" here is a piece of text separated by whitespace. A space, tab, or line
break separates words; several separators together do not create extra words.
Empty text has zero words. Punctuation stays attached, so `Well-made` counts as
one word. This is a simple rule, not a linguistic word detector.

From this folder, run:

```sh
python3 counter.py "Small steps make progress"
python3 -m unittest -v test_counter
```

The app prints `Words: 4`. The seven tests should finish with `OK`. Quotes keep
the whole phrase together as one command-line input. Python puts that input in
`args.text`, passes it to `count_words`, splits it into pieces, counts the pieces
with `len`, then prints the number. The terminal is where you enter commands;
this folder is where `counter.py` and `test_counter.py` must be found.

## The practice-only proposed change

Only one line inside `count_words` changes. The correct baseline is:

```python
    return len(text.split())
```

The deliberately wrong line is:

```python
    return len(text.split(" "))
```

With no argument, `split()` handles runs of whitespace and ignores empty pieces.
With `" "`, it splits only at individual literal spaces. Two spaces introduce an
empty piece, and a tab or line break stays inside a piece. The ordinary four-word
example still prints `Words: 4`, hiding the mistake. Repeated spaces give too
many words; tabs and line breaks give too few. Empty input also incorrectly
counts as one. The tests check those promises instead of relying on one happy
example.

Read a test failure as `actual != expected`: the app's count differs from the
promised count. Four tests fail for this synthetic change: empty text, repeated
spaces, tabs/newlines, and surrounding whitespace. Do not fix the tests to accept
the wrong count. The records checker can still print
`Workspace structure checks passed.` while four application tests fail.
Its JSON says `structure_status: "passed"`,
`verification_scope: "workspace_structure"`, and `application_tests: "not_run"`.
Run the project tests separately; a structure pass does not establish app
behavior or deployment safety.

## Recovery has a small, explicit boundary

First make a copy of this whole practice folder with your file manager and open
that copy. Use a plain-text editor and run all commands from the copied folder.
The release's scripted verifier follows the same exercise in a fresh temporary
folder; its copyable command is in `BEGINNER_GUIDE.md`.

1. Save the baseline before making either edit:

   ```sh
   python3 -c "from pathlib import Path; data = Path('counter.py').read_bytes(); backup = Path('counter.py.before-practice').open('xb'); backup.write(data); backup.close()"
   ```

   The `xb` mode creates a new file only. If this name already exists, Python
   raises `FileExistsError`: stop and use a fresh practice copy. Do not overwrite
   that backup or your current source.

2. Make an unrelated good edit inside `counter.py`: change only the quoted
   `description` text from `Count words separated by whitespace. Put your text in
   quotes.` to `Count words in your draft. Keep the whole phrase in quotes.`
   Save and run:

   ```sh
   python3 counter.py --help
   python3 -m unittest -v test_counter
   ```

   The new help text should appear and all seven tests should still pass. This
   help edit is work you want to keep. You may also create `OPERATOR_NOTES.md`
   with a sentence of your own; that separate file must stay unchanged.

3. Make the deliberate one-line counting mistake described above, save, and
   rerun the app and tests. Expect four failed tests. Keep this failed source
   for inspection using another exclusive copy:

   ```sh
   python3 -c "from pathlib import Path; data = Path('counter.py').read_bytes(); backup = Path('counter.py.practice-bad').open('xb'); backup.write(data); backup.close()"
   ```

   Stop if the failed-source copy already exists. Keep `counter.py` in place.
   Open it and `counter.py.before-practice` side by side. Inspect the differences
   before editing: there should be the wanted help-text edit and the unwanted
   count-line edit. Copying the whole baseline backup over the current source
   would discard the wanted help-text edit.

4. Use the baseline as a reference only. In the current `counter.py`, change
   exactly `return len(text.split(" "))` back to `return len(text.split())`.
   Leave the new help description and any notes untouched. Save and run:

   ```sh
   python3 counter.py --help
   python3 counter.py "Small steps make progress"
   python3 -m unittest -v test_counter
   ```

   Check three things: the new help text remains, the app prints `Words: 4`, and
   all seven tests pass. If you made notes, open them and confirm your sentence
   remains. The scripted verifier also checks recovered bytes against the source
   just before the regression, which already includes the help edit. Recovery
   does not make the source identical to the initial baseline.

This repair changes only the count line in `counter.py`. It does not undo
changes to other files, databases, deployment state, or anything an agent did
elsewhere. It is not a backup system or a safety guarantee. Keep both source
copies until you have reviewed the recovered file and results; no deletion is
needed for this exercise.

## Optional coding-agent prompt

Use this in the copied practice folder if you want an agent to help you explain
the diff. You can complete the exercise without one.

```text
Work only in this copied practice/word-counter folder. Read counter.py,
test_counter.py, CHANGE.md, and the practice source copies if present.
Review this synthetic practice-only diff:
-    return len(text.split())
+    return len(text.split(" "))

Explain in plain words what input the program takes, what will change, which
files would change, and why the simple four-word example can still pass.
List the existing tests that should fail and their expected counts.
Run python3 -m unittest -v test_counter and report the actual result; if the
wrong line is present, explain the failures and show the one-line diff needed
to return to the original counting behavior. The help description
"Count words in your draft. Keep the whole phrase in quotes." is a wanted edit:
preserve it and any OPERATOR_NOTES.md. Explain why a whole-file replacement from
counter.py.before-practice would lose that edit. Do not change files for this
review. Use the backup as a reference only; keep the current source in place.
Do not edit outside this folder, change tests to accept bad results, add
dependencies, use a network or accounts, or delete anything. Say what you
could not verify. A workspace structure pass does not establish app correctness
or deployment safety; application tests are separate.
```

This scripted exercise verifies code and recovery artifacts. It does not show
that a human beginner understood the change or that the kit improved their work.
