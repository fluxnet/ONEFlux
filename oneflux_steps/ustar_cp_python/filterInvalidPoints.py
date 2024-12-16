def filter_invalid_points(
    u_star: np.ndarray,
    f_night: np.ndarray,
    nee: np.ndarray,
    t: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Filter invalid points from u_star and determine annual indices based on conditions.

    Parameters:
    u_star (np.ndarray): Array of u_star values.
    f_night (np.ndarray): Binary array indicating nighttime periods (1 for night, 0 for day).
    nee (np.ndarray): Array of net ecosystem exchange (NEE) values.
    t (np.ndarray): Array of time values.

    Returns:
    Tuple[np.ndarray, np.ndarray, int]:
        - Filtered u_star array with invalid values replaced by NaN.
        - Indices of valid annual points satisfying the conditions.
        - Number of valid annual points.
    """
    # Identify and filter invalid points in u_star (values outside the range [0, 3])
    invalid_indices = np.where((u_star < 0) | (u_star > 3))
    u_star[invalid_indices] = np.nan

    # Find valid annual indices satisfying the given conditions
    valid_annual_indices = np.where((f_night == 1) & ~np.isnan(nee + u_star + t))[0]
    num_valid_annual = len(valid_annual_indices)

    return u_star, valid_annual_indices, num_valid_annual