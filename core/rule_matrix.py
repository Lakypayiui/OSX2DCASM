import random
import time

import numpy as np


class RuleMatrix:
    """Represents a 512-bit cellular automaton rule.

    The rule is stored as a 16x32 matrix of binary values and can be
    converted to or restored from a one-dimensional NumPy array.
    """

    ROWS = 16
    COLS = 32
    SIZE = ROWS * COLS

    def __init__(self) -> None:
        """Initializes an empty rule matrix."""

        self.data: list[list[int]] = [
            [0] * self.COLS
            for _ in range(self.ROWS)
        ]

    def toggle(
        self,
        row: int,
        col: int,
    ) -> None:
        """Toggles the value of a rule cell.

        Args:
            row: Row index of the cell.
            col: Column index of the cell.
        """

        self.data[row][col] ^= 1

    def clear(self) -> None:
        """Clears the entire rule matrix."""

        for row in range(self.ROWS):
            for col in range(self.COLS):
                self.data[row][col] = 0

    def randomize(
        self,
        density: float = 0.4,
    ) -> None:
        """Fills the rule matrix with random values.

        Args:
            density: Probability that a cell will be initialized to 1.
        """

        rng = random.Random(int(time.time()))

        for row in range(self.ROWS):
            for col in range(self.COLS):
                self.data[row][col] = (
                    1 if rng.random() < density else 0
                )

    def set_from_rule_array(
        self,
        rule: np.ndarray,
    ) -> None:
        """Loads the rule matrix from a flattened rule array.

        Args:
            rule: One-dimensional NumPy array containing 512 binary values.
        """

        for index in range(self.SIZE):
            row, col = divmod(index, self.COLS)
            self.data[row][col] = int(rule[index])

    def to_rule_array(self) -> np.ndarray:
        """Converts the rule matrix into a flattened rule array.

        Returns:
            A one-dimensional NumPy array containing the 512 rule bits.
        """

        rule = np.zeros(
            self.SIZE,
            dtype=np.uint8,
        )

        for row in range(self.ROWS):
            for col in range(self.COLS):
                rule[row * self.COLS + col] = (
                    self.data[row][col]
                )

        return rule