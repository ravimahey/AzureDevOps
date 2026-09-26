"""Command-line interface for the securemath package."""

import argparse
import sys
from typing import List, Optional

from securemath import __version__, add, divide, multiply, subtract
from securemath.license import validate_license


def _parse_number(val: str):
    """Convert input string to int or float."""
    try:
        if "." in val or "e" in val.lower():
            return float(val)
        return int(val)
    except ValueError:
        return float(val)


def _format_result(val) -> str:
    """Format numeric result cleanly without unnecessary trailing decimals."""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val)


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="securemath",
        description="securemath - Secure Arithmetic Library CLI",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"securemath {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # add
    add_parser = subparsers.add_parser("add", help="Add two numbers")
    add_parser.add_argument("a", type=_parse_number, help="First operand")
    add_parser.add_argument("b", type=_parse_number, help="Second operand")

    # subtract
    sub_parser = subparsers.add_parser("subtract", help="Subtract two numbers")
    sub_parser.add_argument("a", type=_parse_number, help="First operand")
    sub_parser.add_argument("b", type=_parse_number, help="Second operand")

    # multiply
    mul_parser = subparsers.add_parser("multiply", help="Multiply two numbers")
    mul_parser.add_argument("a", type=_parse_number, help="First operand")
    mul_parser.add_argument("b", type=_parse_number, help="Second operand")

    # divide
    div_parser = subparsers.add_parser("divide", help="Divide two numbers")
    div_parser.add_argument("a", type=_parse_number, help="Numerator")
    div_parser.add_argument("b", type=_parse_number, help="Denominator")

    # license check
    subparsers.add_parser("license", help="Verify current license status")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint function."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "add":
            result = add(args.a, args.b)
            print(_format_result(result))
            return 0

        elif args.command == "subtract":
            result = subtract(args.a, args.b)
            print(_format_result(result))
            return 0

        elif args.command == "multiply":
            result = multiply(args.a, args.b)
            print(_format_result(result))
            return 0

        elif args.command == "divide":
            result = divide(args.a, args.b)
            print(_format_result(result))
            return 0

        elif args.command == "license":
            status = validate_license()
            print(str(status))
            return 0 if status.is_valid else 1

        else:
            parser.print_help()
            return 1

    except ZeroDivisionError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1
    except Exception as err:
        sys.stderr.write(f"Unexpected error: {err}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
