def hamming_weight(string: str) -> int:
    weight = 0
    for x in string:
        assert x in ['0', '1']
        weight = weight + int(x)
    return weight
