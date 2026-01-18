#!/usr/bin/env python3
"""
ChipWhisperer Husky Parameter Test Script

This script connects to the ChipWhisperer Husky and tests all documented
clock glitch, voltage glitch, and shared configuration parameters to verify
they are accessible and functioning correctly.

Based on: GLITCH_PARAMETERS.md

Usage:
    python test_husky_parameters.py [--target] [--verbose]

Options:
    --target    Also connect and test target-related parameters
    --verbose   Show detailed output for each test
"""

import sys
import time
import argparse
from dataclasses import dataclass
from typing import List, Tuple, Any, Optional, Callable

# Add ChipWhisperer to path if needed
try:
    import chipwhisperer as cw
except ImportError:
    print("ERROR: ChipWhisperer not found. Please install or add to PYTHONPATH.")
    sys.exit(1)


@dataclass
class TestResult:
    """Stores the result of a parameter test."""
    parameter: str
    api_path: str
    test_type: str  # 'read', 'write', 'read_write', 'method'
    success: bool
    value_read: Any = None
    value_written: Any = None
    error_message: str = ""
    notes: str = ""


class ParameterTester:
    """Tests ChipWhisperer Husky parameters."""

    def __init__(self, scope, target=None, verbose=False):
        self.scope = scope
        self.target = target
        self.verbose = verbose
        self.results: List[TestResult] = []

    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"  {message}")

    def test_read(self, name: str, api_path: str, getter: Callable) -> TestResult:
        """Test reading a parameter value."""
        try:
            value = getter()
            result = TestResult(
                parameter=name,
                api_path=api_path,
                test_type='read',
                success=True,
                value_read=value
            )
            self.log(f"READ {api_path} = {value}")
        except Exception as e:
            result = TestResult(
                parameter=name,
                api_path=api_path,
                test_type='read',
                success=False,
                error_message=str(e)
            )
            self.log(f"READ {api_path} FAILED: {e}")

        self.results.append(result)
        return result

    def test_write(self, name: str, api_path: str,
                   getter: Callable, setter: Callable,
                   test_values: List[Any],
                   restore_original: bool = True) -> TestResult:
        """Test writing parameter values and reading them back."""
        try:
            # Read original value
            original = getter()
            self.log(f"Original {api_path} = {original}")

            success = True
            tested_values = []

            for test_val in test_values:
                try:
                    setter(test_val)
                    readback = getter()

                    # Check if value was set (with some tolerance for floats)
                    if isinstance(test_val, float):
                        match = abs(readback - test_val) < 0.01 * abs(test_val) if test_val != 0 else abs(readback) < 0.01
                    else:
                        match = readback == test_val

                    tested_values.append((test_val, readback, match))
                    self.log(f"  SET {test_val} -> READ {readback} {'OK' if match else 'MISMATCH'}")

                except Exception as e:
                    tested_values.append((test_val, None, False))
                    self.log(f"  SET {test_val} FAILED: {e}")

            # Restore original value
            if restore_original:
                try:
                    setter(original)
                    self.log(f"Restored {api_path} = {original}")
                except:
                    pass

            # Determine overall success
            success = any(t[2] for t in tested_values)

            result = TestResult(
                parameter=name,
                api_path=api_path,
                test_type='read_write',
                success=success,
                value_read=original,
                value_written=tested_values,
                notes=f"Tested {len(test_values)} values"
            )

        except Exception as e:
            result = TestResult(
                parameter=name,
                api_path=api_path,
                test_type='read_write',
                success=False,
                error_message=str(e)
            )
            self.log(f"WRITE TEST {api_path} FAILED: {e}")

        self.results.append(result)
        return result

    def test_method(self, name: str, api_path: str,
                    method: Callable, args: tuple = ()) -> TestResult:
        """Test calling a method."""
        try:
            result_val = method(*args)
            result = TestResult(
                parameter=name,
                api_path=api_path,
                test_type='method',
                success=True,
                value_read=result_val,
                notes=f"Called with args: {args}"
            )
            self.log(f"METHOD {api_path}({args}) = {result_val}")
        except Exception as e:
            result = TestResult(
                parameter=name,
                api_path=api_path,
                test_type='method',
                success=False,
                error_message=str(e)
            )
            self.log(f"METHOD {api_path}({args}) FAILED: {e}")

        self.results.append(result)
        return result


def test_clock_glitch_parameters(tester: ParameterTester) -> None:
    """Test all clock glitch parameters."""
    scope = tester.scope

    print("\n" + "="*60)
    print("CLOCK GLITCH PARAMETERS")
    print("="*60)

    # IMPORTANT: Enable glitch module first - required for width/offset to work on Husky
    print("\n[0/12] Enabling glitch module (required for width/offset)...")
    scope.glitch.enabled = True
    scope.glitch.clk_src = "pll"  # Must use pll for Husky
    tester.log(f"Glitch enabled: {scope.glitch.enabled}")
    tester.log(f"Glitch clk_src: {scope.glitch.clk_src}")

    # 1. Width (continuous, 0-4592 phase steps)
    print("\n[1/12] Testing Width...")
    tester.test_write(
        "Width", "scope.glitch.width",
        lambda: scope.glitch.width,
        lambda v: setattr(scope.glitch, 'width', v),
        [0, 1000, 2000, 3000, 4592]
    )

    # 2. Offset (continuous, 0-4592 phase steps)
    print("[2/12] Testing Offset...")
    tester.test_write(
        "Offset", "scope.glitch.offset",
        lambda: scope.glitch.offset,
        lambda v: setattr(scope.glitch, 'offset', v),
        [0, 1000, 2000, 3000, 4592]
    )

    # 3. Ext_Offset (integer, 0 - trig_count)
    print("[3/12] Testing Ext_Offset...")
    tester.test_write(
        "Ext_Offset", "scope.glitch.ext_offset",
        lambda: scope.glitch.ext_offset,
        lambda v: setattr(scope.glitch, 'ext_offset', v),
        [0, 10, 50, 100, 500]
    )

    # 4. Repeat (integer, 1-255)
    print("[4/12] Testing Repeat...")
    tester.test_write(
        "Repeat", "scope.glitch.repeat",
        lambda: scope.glitch.repeat,
        lambda v: setattr(scope.glitch, 'repeat', v),
        [1, 5, 10, 50, 255]
    )

    # 5. Clock Source (discrete: pll only on Husky - clkgen is unsupported)
    print("[5/12] Testing Clock Source...")
    # Note: "clkgen" is unsupported on Husky and auto-converts to "pll"
    tester.test_write(
        "Clock Source", "scope.glitch.clk_src",
        lambda: scope.glitch.clk_src,
        lambda v: setattr(scope.glitch, 'clk_src', v),
        ["pll"]  # Only test pll on Husky
    )

    # 6. Output Mode (discrete: clock_xor, clock_or, glitch_only, enable_only)
    print("[6/12] Testing Output Mode...")
    tester.test_write(
        "Output Mode", "scope.glitch.output",
        lambda: scope.glitch.output,
        lambda v: setattr(scope.glitch, 'output', v),
        ["clock_xor", "clock_or", "glitch_only", "enable_only"]
    )

    # 7. Trigger Source (discrete: ext_single, ext_continuous, manual)
    print("[7/12] Testing Trigger Source...")
    tester.test_write(
        "Trigger Source", "scope.glitch.trigger_src",
        lambda: scope.glitch.trigger_src,
        lambda v: setattr(scope.glitch, 'trigger_src', v),
        ["ext_single", "ext_continuous", "manual"]
    )

    # 8. Clock Frequency (continuous, 1MHz - 200MHz+)
    print("[8/12] Testing Clock Frequency...")
    tester.test_write(
        "Clock Frequency", "scope.clock.clkgen_freq",
        lambda: scope.clock.clkgen_freq,
        lambda v: setattr(scope.clock, 'clkgen_freq', v),
        [7.37e6, 24e6, 48e6, 100e6]
    )

    # 9. Phase Shift Steps (read-only)
    print("[9/12] Testing Phase Shift Steps (read-only)...")
    tester.test_read(
        "Phase Shift Steps", "scope.glitch.phase_shift_steps",
        lambda: scope.glitch.phase_shift_steps
    )

    # 10. Glitch Enabled (boolean)
    print("[10/12] Testing Glitch Enabled...")
    tester.test_write(
        "Glitch Enabled", "scope.glitch.enabled",
        lambda: scope.glitch.enabled,
        lambda v: setattr(scope.glitch, 'enabled', v),
        [True, False, True]
    )

    # 11. HS2 Output (discrete: clkgen, glitch)
    print("[11/12] Testing HS2 Output...")
    tester.test_write(
        "HS2 Output", "scope.io.hs2",
        lambda: scope.io.hs2,
        lambda v: setattr(scope.io, 'hs2', v),
        ["clkgen", "glitch"]
    )

    # 12. ARM (method)
    print("[12/12] Testing Arm method...")
    tester.test_method(
        "Arm", "scope.arm()",
        scope.arm
    )


def test_voltage_glitch_parameters(tester: ParameterTester) -> None:
    """Test all voltage glitch parameters."""
    scope = tester.scope

    print("\n" + "="*60)
    print("VOLTAGE GLITCH PARAMETERS")
    print("="*60)

    # 1. vglitch_setup method
    print("\n[1/10] Testing vglitch_setup method...")
    for mode in ['lp', 'hp', 'both']:
        tester.test_method(
            f"vglitch_setup ({mode})", f"scope.vglitch_setup('{mode}')",
            scope.vglitch_setup,
            (mode, False)  # default_setup=False to avoid changing other settings
        )

    # 2. LP MOSFET (boolean)
    print("[2/10] Testing LP MOSFET...")
    tester.test_write(
        "LP MOSFET", "scope.io.glitch_lp",
        lambda: scope.io.glitch_lp,
        lambda v: setattr(scope.io, 'glitch_lp', v),
        [True, False, True]
    )

    # 3. HP MOSFET (boolean)
    print("[3/10] Testing HP MOSFET...")
    tester.test_write(
        "HP MOSFET", "scope.io.glitch_hp",
        lambda: scope.io.glitch_hp,
        lambda v: setattr(scope.io, 'glitch_hp', v),
        [True, False, True]
    )

    # 4. Output Mode for voltage (glitch_only, enable_only)
    print("[4/10] Testing Output Mode (voltage)...")
    tester.test_write(
        "Output Mode (Voltage)", "scope.glitch.output",
        lambda: scope.glitch.output,
        lambda v: setattr(scope.glitch, 'output', v),
        ["glitch_only", "enable_only"]
    )

    # 5. vglitch_reset method
    print("[5/10] Testing vglitch_reset method...")
    tester.test_method(
        "vglitch_reset", "scope.io.vglitch_reset()",
        scope.io.vglitch_reset
    )

    # Note: Width, Offset, Ext_Offset, Repeat are already tested in clock section
    # They use the same registers for voltage glitching
    print("[6/10] Width - Same as clock glitch (already tested)")
    print("[7/10] Offset - Same as clock glitch (already tested)")
    print("[8/10] Ext_Offset - Same as clock glitch (already tested)")
    print("[9/10] Repeat - Same as clock glitch (already tested)")
    print("[10/10] Trigger Source - Same as clock glitch (already tested)")


def test_shared_parameters(tester: ParameterTester) -> None:
    """Test shared configuration parameters."""
    scope = tester.scope

    print("\n" + "="*60)
    print("SHARED CONFIGURATION PARAMETERS")
    print("="*60)

    # 1. ADC Samples
    print("\n[1/8] Testing ADC Samples...")
    tester.test_write(
        "ADC Samples", "scope.adc.samples",
        lambda: scope.adc.samples,
        lambda v: setattr(scope.adc, 'samples', v),
        [1000, 5000, 24000, 50000]
    )

    # 2. ADC Timeout
    print("[2/8] Testing ADC Timeout...")
    tester.test_write(
        "ADC Timeout", "scope.adc.timeout",
        lambda: scope.adc.timeout,
        lambda v: setattr(scope.adc, 'timeout', v),
        [0.5, 1.0, 2.0, 5.0]
    )

    # 3. Trigger Module
    print("[3/8] Testing Trigger Module...")
    tester.test_write(
        "Trigger Module", "scope.trigger.module",
        lambda: scope.trigger.module,
        lambda v: setattr(scope.trigger, 'module', v),
        ["basic"]
    )

    # 4. Target Reset (nrst)
    print("[4/8] Testing Target Reset...")
    tester.test_write(
        "Target Reset", "scope.io.nrst",
        lambda: scope.io.nrst,
        lambda v: setattr(scope.io, 'nrst', v),
        ["high_z", "low", "high_z"]
    )

    # 5. ADC Trig Count (read-only)
    print("[5/8] Testing ADC Trig Count (read-only)...")
    tester.test_read(
        "ADC Trig Count", "scope.adc.trig_count",
        lambda: scope.adc.trig_count
    )

    # 6. ADC State (read-only)
    print("[6/8] Testing ADC State (read-only)...")
    tester.test_read(
        "ADC State", "scope.adc.state",
        lambda: scope.adc.state
    )

    # 7. ADC Lo Gain Errors Disabled
    print("[7/8] Testing ADC Lo Gain Errors Disabled...")
    tester.test_write(
        "ADC Lo Gain Errors Disabled", "scope.adc.lo_gain_errors_disabled",
        lambda: scope.adc.lo_gain_errors_disabled,
        lambda v: setattr(scope.adc, 'lo_gain_errors_disabled', v),
        [True, False, True]
    )

    # 8. ADC Clip Errors Disabled
    print("[8/8] Testing ADC Clip Errors Disabled...")
    tester.test_write(
        "ADC Clip Errors Disabled", "scope.adc.clip_errors_disabled",
        lambda: scope.adc.clip_errors_disabled,
        lambda v: setattr(scope.adc, 'clip_errors_disabled', v),
        [True, False, True]
    )


def test_target_parameters(tester: ParameterTester) -> None:
    """Test target-related parameters."""
    target = tester.target

    if target is None:
        print("\n" + "="*60)
        print("TARGET PARAMETERS (SKIPPED - no target connected)")
        print("="*60)
        return

    print("\n" + "="*60)
    print("TARGET PARAMETERS")
    print("="*60)

    # 1. Baud Rate
    print("\n[1/2] Testing Baud Rate...")
    tester.test_write(
        "Baud Rate", "target.baud",
        lambda: target.baud,
        lambda v: setattr(target, 'baud', v),
        [38400, 115200, 230400]
    )

    # 2. In Waiting (read-only)
    print("[2/2] Testing In Waiting (read-only)...")
    tester.test_read(
        "In Waiting", "target.in_waiting()",
        lambda: target.in_waiting()
    )


def test_husky_specific(tester: ParameterTester) -> None:
    """Test Husky-specific features."""
    scope = tester.scope

    print("\n" + "="*60)
    print("HUSKY-SPECIFIC PARAMETERS")
    print("="*60)

    # Check if this is actually a Husky
    is_husky = hasattr(scope, '_is_husky') and scope._is_husky
    print(f"\nDevice is Husky: {is_husky}")

    if not is_husky:
        print("Skipping Husky-specific tests...")
        return

    # 1. Clkgen Source (Husky uses clkgen_src instead of adc_src)
    print("\n[1/6] Testing Clkgen Source...")
    tester.test_write(
        "Clkgen Source", "scope.clock.clkgen_src",
        lambda: scope.clock.clkgen_src,
        lambda v: setattr(scope.clock, 'clkgen_src', v),
        ["system", "extclk"]
    )

    # 2. ADC Mul (Husky uses adc_mul instead of adc_src)
    print("[2/6] Testing ADC Mul...")
    tester.test_write(
        "ADC Mul", "scope.clock.adc_mul",
        lambda: scope.clock.adc_mul,
        lambda v: setattr(scope.clock, 'adc_mul', v),
        [1, 2, 4]
    )

    # 3. PLL lock status (read-only)
    print("[3/6] Testing PLL Lock Status...")
    tester.test_read(
        "PLL Locked", "scope.clock.pll.pll_locked",
        lambda: scope.clock.pll.pll_locked if hasattr(scope.clock, 'pll') else None
    )

    # 4. Glitch MMCM locked status
    print("[4/6] Testing Glitch MMCM Locked...")
    tester.test_read(
        "Glitch MMCM Locked", "scope.glitch.mmcm_locked",
        lambda: scope.glitch.mmcm_locked if hasattr(scope.glitch, 'mmcm_locked') else None
    )

    # 5. ADC Frequency (read-only)
    print("[5/6] Testing ADC Frequency...")
    tester.test_read(
        "ADC Frequency", "scope.clock.adc_freq",
        lambda: scope.clock.adc_freq
    )

    # 6. Check scope name/version
    print("[6/6] Testing Scope Info...")
    tester.test_read(
        "Scope Name", "scope.getName()",
        lambda: scope.getName() if hasattr(scope, 'getName') else "Unknown"
    )


def print_summary(results: List[TestResult]) -> Tuple[int, int, int]:
    """Print a summary of all test results."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({100*passed/total:.1f}%)" if total > 0 else "Passed: 0")
    print(f"Failed: {failed} ({100*failed/total:.1f}%)" if total > 0 else "Failed: 0")

    # Print failed tests
    if failed > 0:
        print("\n--- FAILED TESTS ---")
        for r in results:
            if not r.success:
                print(f"  {r.parameter}")
                print(f"    API: {r.api_path}")
                print(f"    Error: {r.error_message}")

    # Print passed tests with values
    print("\n--- PASSED TESTS ---")
    for r in results:
        if r.success:
            if r.test_type == 'read':
                print(f"  {r.parameter}: {r.value_read}")
            elif r.test_type == 'read_write':
                print(f"  {r.parameter}: {r.value_read} (original)")
            elif r.test_type == 'method':
                print(f"  {r.parameter}: OK")

    return passed, failed, total


def print_parameter_table(results: List[TestResult]) -> None:
    """Print results in a table format suitable for documentation."""
    print("\n" + "="*60)
    print("PARAMETER VERIFICATION TABLE")
    print("="*60)

    print("\n| Parameter | API Path | Status | Value/Notes |")
    print("|-----------|----------|--------|-------------|")

    for r in results:
        # Use ASCII-safe characters for Windows console compatibility
        status = "[PASS]" if r.success else "[FAIL]"
        if r.success:
            if r.test_type == 'read':
                notes = str(r.value_read)
            elif r.test_type == 'read_write':
                notes = f"Original: {r.value_read}"
            else:
                notes = "Method OK"
        else:
            notes = r.error_message[:30] + "..." if len(r.error_message) > 30 else r.error_message

        # Truncate and format safely
        param = r.parameter[:25] if r.parameter else ""
        api = r.api_path[:30] if r.api_path else ""
        notes = str(notes)[:30] if notes else ""
        print(f"| {param:25} | {api:30} | {status:6} | {notes:30} |")


def main():
    parser = argparse.ArgumentParser(
        description="Test ChipWhisperer Husky parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_husky_parameters.py              # Basic test, scope only
    python test_husky_parameters.py --target     # Also test target parameters
    python test_husky_parameters.py --verbose    # Show detailed output
        """
    )
    parser.add_argument('--target', action='store_true',
                        help='Connect and test target parameters')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output for each test')
    parser.add_argument('--platform', default='CW308_SAM4S',
                        help='Target platform (default: CW308_SAM4S)')

    args = parser.parse_args()

    print("="*60)
    print("ChipWhisperer Husky Parameter Test")
    print("="*60)
    print(f"\nChipWhisperer version: {cw.__version__}")
    print(f"Verbose mode: {args.verbose}")
    print(f"Test target: {args.target}")

    # Connect to scope
    print("\nConnecting to ChipWhisperer Husky...")
    try:
        scope = cw.scope()
        print(f"  Connected: {scope.getName() if hasattr(scope, 'getName') else 'Unknown'}")
        print(f"  Is Husky: {scope._is_husky if hasattr(scope, '_is_husky') else 'Unknown'}")
    except Exception as e:
        print(f"ERROR: Failed to connect to scope: {e}")
        sys.exit(1)

    # Connect to target if requested
    target = None
    if args.target:
        print("\nConnecting to target...")
        try:
            target = cw.target(scope, cw.targets.SimpleSerial2)
            print(f"  Connected: SimpleSerial2")
        except Exception as e:
            print(f"WARNING: Failed to connect to target: {e}")
            print("  Continuing without target...")

    # Create tester
    tester = ParameterTester(scope, target, verbose=args.verbose)

    # Run all tests
    try:
        # Basic scope setup for testing
        print("\nInitializing scope for testing...")
        scope.default_setup()

        # Run test categories
        test_clock_glitch_parameters(tester)
        test_voltage_glitch_parameters(tester)
        test_shared_parameters(tester)
        test_target_parameters(tester)
        test_husky_specific(tester)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()

    # Print results
    passed, failed, total = print_summary(tester.results)
    print_parameter_table(tester.results)

    # Cleanup
    print("\nCleaning up...")
    try:
        if target:
            target.dis()
        scope.dis()
        print("  Disconnected successfully.")
    except:
        pass

    # Exit code based on results
    if failed > 0:
        print(f"\n{failed} tests failed!")
        sys.exit(1)
    else:
        print(f"\nAll {passed} tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
