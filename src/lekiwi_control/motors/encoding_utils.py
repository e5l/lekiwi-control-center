#!/usr/bin/env python

# ABOUTME: Encoding utilities for motor communication
# ABOUTME: Provides sign-magnitude conversion for motor values


def encode_sign_magnitude(value: int | float, sign_bit: int) -> int:
    """
    Encode a signed value into sign-magnitude representation.

    Args:
        value: The signed value to encode
        sign_bit: The bit position for the sign (0-indexed from LSB)

    Returns:
        The encoded unsigned integer value

    Examples:
        >>> encode_sign_magnitude(-100, 15)  # sign bit at position 15
        32868  # 0x8064 = sign bit set + magnitude 100
        >>> encode_sign_magnitude(100, 15)
        100    # 0x0064 = sign bit clear + magnitude 100
    """
    if value < 0:
        # Set the sign bit and use absolute value as magnitude
        return int(abs(value)) | (1 << sign_bit)
    else:
        # Positive value, just return magnitude
        return int(value)


def decode_sign_magnitude(value: int, sign_bit: int) -> int:
    """
    Decode a sign-magnitude encoded value into a signed integer.

    Args:
        value: The unsigned encoded value
        sign_bit: The bit position for the sign (0-indexed from LSB)

    Returns:
        The decoded signed integer value

    Examples:
        >>> decode_sign_magnitude(32868, 15)  # 0x8064
        -100
        >>> decode_sign_magnitude(100, 15)    # 0x0064
        100
    """
    # Create a mask for the sign bit
    sign_mask = 1 << sign_bit
    # Create a mask for the magnitude (all bits below sign bit)
    magnitude_mask = sign_mask - 1

    # Extract the sign and magnitude
    is_negative = bool(value & sign_mask)
    magnitude = value & magnitude_mask

    # Return signed value
    return -magnitude if is_negative else magnitude
