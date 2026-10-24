
import hashlib
import json
import datetime
import math
import re

import pandas as pd


_DATE_PATTERN = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}")


def _norm(value):
    """Normalize values so SQL results can be fingerprinted consistently."""

    if value is None:
        return None

    if isinstance(value, (datetime.date, datetime.datetime, pd.Timestamp)):
        return pd.Timestamp(value).date().isoformat()

    if isinstance(value, str):
        value = value.strip()

        if _DATE_PATTERN.match(value):
            try:
                return pd.Timestamp(value).date().isoformat()
            except (ValueError, TypeError):
                pass

        return value

    try:
        if math.isnan(value):
            return None
    except (TypeError, ValueError):
        pass

    try:
        return round(float(value), 2)
    except (TypeError, ValueError, OverflowError):
        return str(value)


def _fingerprint(df):
    """Create a consistent fingerprint of the returned rows."""

    rows = [
        [_norm(value) for value in row]
        for row in df.itertuples(index=False, name=None)
    ]

    return hashlib.sha256(
        json.dumps(rows).encode("utf-8")
    ).hexdigest()


class Practice:

    def __init__(self, expected, titles):
        self.expected = expected
        self.titles = titles

        # None = not attempted, True = correct, False = incorrect
        self.results = {
            task_id: None for task_id in expected
        }

    def sql(self, task_id, query_str):
        """Run a query and check its shape and fingerprint."""

        from db.dataraflow_db import run_query

        if task_id not in self.expected:
            raise KeyError(f"Unknown task ID: {task_id}")

        print(
            f"\nRunning {task_id}: "
            f"{self.titles.get(task_id, '')}"
        )

        if not isinstance(query_str, str) or not query_str.strip():
            self.results[task_id] = None
            print("⏳ Not attempted yet. Please provide a SQL query.")
            return

        try:
            df = run_query(query_str)

        except Exception as error:
            self.results[task_id] = False
            print(
                f"❌ Query execution failed: "
                f"{type(error).__name__}: {str(error)[:300]}"
            )
            return

        expected_shape, expected_hash = self.expected[task_id]

        # Check the number of rows and columns.
        if list(df.shape) != expected_shape:
            self.results[task_id] = False

            print(
                f"❌ Incorrect shape. Expected "
                f"{expected_shape[0]} row(s) × "
                f"{expected_shape[1]} column(s), "
                f"but received {df.shape[0]} × {df.shape[1]}."
            )

            try:
                display(df.head(15))
            except NameError:
                print(df.head(15))

            return

        # Check the actual data, not just the shape.
        actual_hash = _fingerprint(df)
        is_correct = actual_hash == expected_hash

        self.results[task_id] = is_correct

        try:
            display(df.head(15))
        except NameError:
            print(df.head(15))

        if is_correct:
            print(f"✅ {task_id}: Correct!")
        else:
            print(
                f"❌ {task_id}: Incorrect answer. "
                "The shape is correct, but the data fingerprint "
                "does not match."
            )
            print(
                "Check the selected columns, sorting, date conversion, "
                "rounding, filters, and NULL handling."
            )

    def score(self):
        """Display results and calculate the total score."""

        rows = []

        for task_id in self.expected:
            result = self.results[task_id]

            if result is True:
                status = "Correct"
            elif result is False:
                status = "Incorrect"
            else:
                status = "Not attempted"

            rows.append([
                task_id,
                self.titles.get(task_id, ""),
                status
            ])

        results_df = pd.DataFrame(
            rows,
            columns=["Task", "Topic", "Result"]
        )

        print("\n========== SQL PRACTICE SCORE ==========")
        print(results_df.to_string(index=False))

        correct = sum(
            result is True for result in self.results.values()
        )
        total = len(self.expected)
        attempted = sum(
            result is not None for result in self.results.values()
        )

        percentage = (correct / total * 100) if total else 0.0

        print(f"\nCorrect answers: {correct}")
        print(f"Tasks attempted: {attempted}/{total}")
        print(f"Total score: {correct}/{total}")
        print(f"Percentage: {percentage:.1f}%")

        return {
            "correct": correct,
            "total": total,
            "attempted": attempted,
            "percentage": round(percentage, 1),
            "results": results_df
        }

    def sql_score(self):
        """Alias for score(), matching your previous assessment."""

        return self.score()
