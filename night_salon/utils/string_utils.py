def normalize_name(name):
    """Convert a name to a consistent format for lookups

    Handles various name formats and normalizes to capitalized form (first letter uppercase, rest lowercase)

    Args:
        name: String or object with a name attribute to normalize

    Returns:
        Normalized string in Capitalized format
    """
    if hasattr(name, "name"):
        # If it's an enum or similar with a name attribute, use that
        return name.name.lower().capitalize()
    else:
        # Otherwise assume it's a string and normalize
        return str(name).lower().capitalize()
