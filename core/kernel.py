from core.rule_matrix import RuleMatrix
import numpy as np


class Kernel:
    """Represents a 3x3 Moore neighborhood kernel.

    The kernel stores the state of its nine cells as bits and provides
    utility methods to manipulate the kernel and generate a rule array
    compatible with the cellular automaton.
    """

    def __init__(self) -> None:
        """Initializes an empty kernel."""

        self.bits: list[int] = [0] * 9

    @property
    def mask(self) -> int:
        """Returns the kernel encoded as a 9-bit integer."""

        mask = 0

        for index, bit in enumerate(self.bits):
            mask |= bit << index

        return mask

    def toggle(self, index: int) -> None:
        """Toggles the value of a kernel cell.

        Args:
            index: Index of the kernel cell to toggle (0-8).
        """

        self.bits[index] ^= 1

    def set_mask(self, mask: int) -> None:
        """Loads the kernel from a 9-bit mask.

        Args:
            mask: Integer representation of the kernel.

        Raises:
            ValueError: If ``mask`` is outside the valid range [0, 511].
        """

        if not 0 <= mask <= 0x1FF:
            raise ValueError(
                "Kernel mask must be a 9-bit integer (0-511)."
            )

        for index in range(9):
            self.bits[index] = (mask >> index) & 1

    def apply_to_matrix(
        self,
        rule_matrix: RuleMatrix,
    ) -> np.ndarray:
        """Applies the kernel to a rule matrix.

        The current kernel mask is used to activate the corresponding
        entry in the 512-bit rule matrix.

        Args:
            rule_matrix: Rule matrix to modify.

        Returns:
            A NumPy array representing the updated rule.
        """

        mask = self.mask

        rule_matrix.data[mask // 32][mask % 32] = 1

        return rule_matrix.to_rule_array()

    def clear(self) -> None:
        """Clears all kernel bits."""

        self.bits = [0] * 9