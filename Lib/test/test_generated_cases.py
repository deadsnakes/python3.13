import contextlib
import os
import sys
import tempfile
import unittest

from test import support
from test import test_tools


def skip_if_different_mount_drives():
    if sys.platform != 'win32':
        return
    ROOT = os.path.dirname(os.path.dirname(__file__))
    root_drive = os.path.splitroot(ROOT)[0]
    cwd_drive = os.path.splitroot(os.getcwd())[0]
    if root_drive != cwd_drive:
        # generate_cases.py uses relpath() which raises ValueError if ROOT
        # and the current working different have different mount drives
        # (on Windows).
        raise unittest.SkipTest(
            f"the current working directory and the Python source code "
            f"directory have different mount drives "
            f"({cwd_drive} and {root_drive})"
        )
skip_if_different_mount_drives()


test_tools.skip_if_missing('cases_generator')
with test_tools.imports_under_tool('cases_generator'):
    import generate_cases
    import analysis
    import formatting
    from parsing import StackEffect


def handle_stderr():
    if support.verbose > 1:
        return contextlib.nullcontext()
    else:
        return support.captured_stderr()

class TestEffects(unittest.TestCase):
    def test_effect_sizes(self):
        input_effects = [
            x := StackEffect("x", "", "", ""),
            y := StackEffect("y", "", "", "oparg"),
            z := StackEffect("z", "", "", "oparg*2"),
        ]
        output_effects = [
            StackEffect("a", "", "", ""),
            StackEffect("b", "", "", "oparg*4"),
            StackEffect("c", "", "", ""),
        ]
        other_effects = [
            StackEffect("p", "", "", "oparg<<1"),
            StackEffect("q", "", "", ""),
            StackEffect("r", "", "", ""),
        ]
        self.assertEqual(formatting.effect_size(x), (1, ""))
        self.assertEqual(formatting.effect_size(y), (0, "oparg"))
        self.assertEqual(formatting.effect_size(z), (0, "oparg*2"))

        self.assertEqual(
            formatting.list_effect_size(input_effects),
            (1, "oparg + oparg*2"),
        )
        self.assertEqual(
            formatting.list_effect_size(output_effects),
            (2, "oparg*4"),
        )
        self.assertEqual(
            formatting.list_effect_size(other_effects),
            (2, "(oparg<<1)"),
        )


class TestGeneratedCases(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.maxDiff = None

        self.temp_dir = tempfile.gettempdir()
        self.temp_input_filename = os.path.join(self.temp_dir, "input.txt")
        self.temp_output_filename = os.path.join(self.temp_dir, "output.txt")
        self.temp_metadata_filename = os.path.join(self.temp_dir, "metadata.txt")
        self.temp_pymetadata_filename = os.path.join(self.temp_dir, "pymetadata.txt")
        self.temp_executor_filename = os.path.join(self.temp_dir, "executor.txt")

    def tearDown(self) -> None:
        for filename in [
            self.temp_input_filename,
            self.temp_output_filename,
            self.temp_metadata_filename,
            self.temp_pymetadata_filename,
            self.temp_executor_filename,
        ]:
            try:
                os.remove(filename)
            except:
                pass
        super().tearDown()

    def run_cases_test(self, input: str, expected: str):
        with open(self.temp_input_filename, "w+") as temp_input:
            temp_input.write(analysis.BEGIN_MARKER)
            temp_input.write(input)
            temp_input.write(analysis.END_MARKER)
            temp_input.flush()

        a = generate_cases.Generator([self.temp_input_filename])
        with handle_stderr():
            a.parse()
            a.analyze()
            if a.errors:
                raise RuntimeError(f"Found {a.errors} errors")
            a.write_instructions(self.temp_output_filename, False)

        with open(self.temp_output_filename) as temp_output:
            lines = temp_output.readlines()
            while lines and lines[0].startswith("// "):
                lines.pop(0)
        actual = "".join(lines)
        # if actual.rstrip() != expected.rstrip():
        #     print("Actual:")
        #     print(actual)
        #     print("Expected:")
        #     print(expected)
        #     print("End")

        self.assertEqual(actual.rstrip(), expected.rstrip())

    def test_inst_no_args(self):
        input = """
        inst(OP, (--)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            spam();
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_inst_one_pop(self):
        input = """
        inst(OP, (value --)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            PyObject *value;
            value = stack_pointer[-1];
            spam();
            STACK_SHRINK(1);
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_inst_one_push(self):
        input = """
        inst(OP, (-- res)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            PyObject *res;
            spam();
            STACK_GROW(1);
            stack_pointer[-1] = res;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_inst_one_push_one_pop(self):
        input = """
        inst(OP, (value -- res)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            PyObject *value;
            PyObject *res;
            value = stack_pointer[-1];
            spam();
            stack_pointer[-1] = res;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_binary_op(self):
        input = """
        inst(OP, (left, right -- res)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            PyObject *right;
            PyObject *left;
            PyObject *res;
            right = stack_pointer[-1];
            left = stack_pointer[-2];
            spam();
            STACK_SHRINK(1);
            stack_pointer[-1] = res;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_overlap(self):
        input = """
        inst(OP, (left, right -- left, result)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            PyObject *right;
            PyObject *left;
            PyObject *result;
            right = stack_pointer[-1];
            left = stack_pointer[-2];
            spam();
            stack_pointer[-1] = result;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_predictions_and_eval_breaker(self):
        input = """
        inst(OP1, (arg -- rest)) {
        }
        inst(OP3, (arg -- res)) {
            DEOPT_IF(xxx);
            CHECK_EVAL_BREAKER();
        }
        family(OP1, INLINE_CACHE_ENTRIES_OP1) = { OP3 };
    """
        output = """
        TARGET(OP1) {
            PREDICTED(OP1);
            static_assert(INLINE_CACHE_ENTRIES_OP1 == 0, "incorrect cache size");
            PyObject *arg;
            PyObject *rest;
            arg = stack_pointer[-1];
            stack_pointer[-1] = rest;
            DISPATCH();
        }

        TARGET(OP3) {
            PyObject *arg;
            PyObject *res;
            arg = stack_pointer[-1];
            DEOPT_IF(xxx, OP1);
            stack_pointer[-1] = res;
            CHECK_EVAL_BREAKER();
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_error_if_plain(self):
        input = """
        inst(OP, (--)) {
            ERROR_IF(cond, label);
        }
    """
        output = """
        TARGET(OP) {
            if (cond) goto label;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_error_if_plain_with_comment(self):
        input = """
        inst(OP, (--)) {
            ERROR_IF(cond, label);  // Comment is ok
        }
    """
        output = """
        TARGET(OP) {
            if (cond) goto label;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_error_if_pop(self):
        input = """
        inst(OP, (left, right -- res)) {
            ERROR_IF(cond, label);
        }
    """
        output = """
        TARGET(OP) {
            PyObject *right;
            PyObject *left;
            PyObject *res;
            right = stack_pointer[-1];
            left = stack_pointer[-2];
            if (cond) goto pop_2_label;
            STACK_SHRINK(1);
            stack_pointer[-1] = res;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_cache_effect(self):
        input = """
        inst(OP, (counter/1, extra/2, value --)) {
        }
    """
        output = """
        TARGET(OP) {
            PyObject *value;
            value = stack_pointer[-1];
            uint16_t counter = read_u16(&next_instr[0].cache);
            uint32_t extra = read_u32(&next_instr[1].cache);
            STACK_SHRINK(1);
            next_instr += 3;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_suppress_dispatch(self):
        input = """
        inst(OP, (--)) {
            goto somewhere;
        }
    """
        output = """
        TARGET(OP) {
            goto somewhere;
        }
    """
        self.run_cases_test(input, output)

    def test_macro_instruction(self):
        input = """
        inst(OP1, (counter/1, left, right -- left, right)) {
            op1(left, right);
        }
        op(OP2, (extra/2, arg2, left, right -- res)) {
            res = op2(arg2, left, right);
        }
        macro(OP) = OP1 + cache/2 + OP2;
        inst(OP3, (unused/5, arg2, left, right -- res)) {
            res = op3(arg2, left, right);
        }
        family(OP, INLINE_CACHE_ENTRIES_OP) = { OP3 };
    """
        output = """
        TARGET(OP1) {
            PyObject *right;
            PyObject *left;
            right = stack_pointer[-1];
            left = stack_pointer[-2];
            uint16_t counter = read_u16(&next_instr[0].cache);
            op1(left, right);
            next_instr += 1;
            DISPATCH();
        }

        TARGET(OP) {
            PREDICTED(OP);
            static_assert(INLINE_CACHE_ENTRIES_OP == 5, "incorrect cache size");
            PyObject *right;
            PyObject *left;
            PyObject *arg2;
            PyObject *res;
            // OP1
            right = stack_pointer[-1];
            left = stack_pointer[-2];
            {
                uint16_t counter = read_u16(&next_instr[0].cache);
                op1(left, right);
            }
            // OP2
            arg2 = stack_pointer[-3];
            {
                uint32_t extra = read_u32(&next_instr[3].cache);
                res = op2(arg2, left, right);
            }
            STACK_SHRINK(2);
            stack_pointer[-1] = res;
            next_instr += 5;
            DISPATCH();
        }

        TARGET(OP3) {
            PyObject *right;
            PyObject *left;
            PyObject *arg2;
            PyObject *res;
            right = stack_pointer[-1];
            left = stack_pointer[-2];
            arg2 = stack_pointer[-3];
            res = op3(arg2, left, right);
            STACK_SHRINK(2);
            stack_pointer[-1] = res;
            next_instr += 5;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_array_input(self):
        input = """
        inst(OP, (below, values[oparg*2], above --)) {
            spam();
        }
    """
        output = """
        TARGET(OP) {
            PyObject *above;
            PyObject **values;
            PyObject *below;
            above = stack_pointer[-1];
            values = stack_pointer - 1 - oparg*2;
            below = stack_pointer[-2 - oparg*2];
            spam();
            STACK_SHRINK(oparg*2);
            STACK_SHRINK(2);
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_array_output(self):
        input = """
        inst(OP, (unused, unused -- below, values[oparg*3], above)) {
            spam(values, oparg);
        }
    """
        output = """
        TARGET(OP) {
            PyObject *below;
            PyObject **values;
            PyObject *above;
            values = stack_pointer - 1;
            spam(values, oparg);
            STACK_GROW(oparg*3);
            stack_pointer[-2 - oparg*3] = below;
            stack_pointer[-1] = above;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_array_input_output(self):
        input = """
        inst(OP, (values[oparg] -- values[oparg], above)) {
            spam(values, oparg);
        }
    """
        output = """
        TARGET(OP) {
            PyObject **values;
            PyObject *above;
            values = stack_pointer - oparg;
            spam(values, oparg);
            STACK_GROW(1);
            stack_pointer[-1] = above;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_array_error_if(self):
        input = """
        inst(OP, (extra, values[oparg] --)) {
            ERROR_IF(oparg == 0, somewhere);
        }
    """
        output = """
        TARGET(OP) {
            PyObject **values;
            PyObject *extra;
            values = stack_pointer - oparg;
            extra = stack_pointer[-1 - oparg];
            if (oparg == 0) { STACK_SHRINK(oparg); goto pop_1_somewhere; }
            STACK_SHRINK(oparg);
            STACK_SHRINK(1);
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_cond_effect(self):
        input = """
        inst(OP, (aa, input if ((oparg & 1) == 1), cc -- xx, output if (oparg & 2), zz)) {
            output = spam(oparg, input);
        }
    """
        output = """
        TARGET(OP) {
            PyObject *cc;
            PyObject *input = NULL;
            PyObject *aa;
            PyObject *xx;
            PyObject *output = NULL;
            PyObject *zz;
            cc = stack_pointer[-1];
            if ((oparg & 1) == 1) { input = stack_pointer[-1 - ((oparg & 1) == 1 ? 1 : 0)]; }
            aa = stack_pointer[-2 - ((oparg & 1) == 1 ? 1 : 0)];
            output = spam(oparg, input);
            STACK_SHRINK((((oparg & 1) == 1) ? 1 : 0));
            STACK_GROW(((oparg & 2) ? 1 : 0));
            stack_pointer[-2 - (oparg & 2 ? 1 : 0)] = xx;
            if (oparg & 2) { stack_pointer[-1 - (oparg & 2 ? 1 : 0)] = output; }
            stack_pointer[-1] = zz;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_macro_cond_effect(self):
        input = """
        op(A, (left, middle, right --)) {
            # Body of A
        }
        op(B, (-- deep, extra if (oparg), res)) {
            # Body of B
        }
        macro(M) = A + B;
    """
        output = """
        TARGET(M) {
            PyObject *right;
            PyObject *middle;
            PyObject *left;
            PyObject *deep;
            PyObject *extra = NULL;
            PyObject *res;
            // A
            right = stack_pointer[-1];
            middle = stack_pointer[-2];
            left = stack_pointer[-3];
            {
                # Body of A
            }
            // B
            {
                # Body of B
            }
            STACK_SHRINK(1);
            STACK_GROW((oparg ? 1 : 0));
            stack_pointer[-2 - (oparg ? 1 : 0)] = deep;
            if (oparg) { stack_pointer[-1 - (oparg ? 1 : 0)] = extra; }
            stack_pointer[-1] = res;
            DISPATCH();
        }
    """
        self.run_cases_test(input, output)

    def test_macro_push_push(self):
        input = """
        op(A, (-- val1)) {
            val1 = spam();
        }
        op(B, (-- val2)) {
            val2 = spam();
        }
        macro(M) = A + B;
        """
        output = """
        TARGET(M) {
            PyObject *val1;
            PyObject *val2;
            // A
            {
                val1 = spam();
            }
            // B
            {
                val2 = spam();
            }
            STACK_GROW(2);
            stack_pointer[-2] = val1;
            stack_pointer[-1] = val2;
            DISPATCH();
        }
        """
        self.run_cases_test(input, output)

    def test_override_inst(self):
        input = """
        inst(OP, (--)) {
            spam();
        }
        override inst(OP, (--)) {
            ham();
        }
        """
        output = """
        TARGET(OP) {
            ham();
            DISPATCH();
        }
        """
        self.run_cases_test(input, output)

    def test_override_op(self):
        input = """
        op(OP, (--)) {
            spam();
        }
        macro(M) = OP;
        override op(OP, (--)) {
            ham();
        }
        """
        output = """
        TARGET(M) {
            ham();
            DISPATCH();
        }
        """
        self.run_cases_test(input, output)


if __name__ == "__main__":
    unittest.main()
