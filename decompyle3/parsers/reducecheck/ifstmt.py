#  Copyright (c) 2020 Rocky Bernstein


def ifstmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    if lhs == "ifstmtc":
        if last == n:
            last -= 1
            pass
        if tokens[last].attr and isinstance(tokens[last].attr, int):
            return tokens[first].offset < tokens[last].attr
        pass

    # Make sure jumps don't extend beyond the end of the if statement.
    l = last
    if l == n:
        l -= 1
    if isinstance(tokens[l].offset, str):
        last_offset = int(tokens[l].offset.split("_")[0], 10)
    else:
        last_offset = tokens[l].offset
    for i in range(first, l):
        t = tokens[i]
        # instead of POP_JUMP_IF, should we use op attributes?
        if t.kind in ("POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE"):
            pjif_target = t.attr
            if pjif_target > last_offset:
                # In come cases, where we have long bytecode, a
                # "POP_JUMP_IF_TRUE/FALSE" offset might be too
                # large for the instruction; so instead it
                # jumps to a JUMP_FORWARD. Allow that here.
                if tokens[l] == "JUMP_FORWARD":
                    return tokens[l].attr != pjif_target
                return True
            elif lhs == "ifstmtc" and tokens[first].off2int() > pjif_target:
                # A conditional JUMP to the loop is expected for "ifstmtc"
                return False
            pass
        pass
    pass

    if ast:
        testexpr = ast[0]

        if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
            # iflastsmtl jumped outside of loop. No good.
            return True

        if testexpr[0] in ("testtrue", "testfalse"):
            test = testexpr[0]
            if len(test) > 1 and test[1].kind.startswith("jmp_"):
                jmp_target = test[1][0].attr
                if (
                    tokens[first].off2int(prefer_last=True)
                    <= jmp_target
                    < tokens[last].off2int(prefer_last=False)
                ):
                    return True
                # jmp_target less than tokens[first] is okay - is to a loop
                # jmp_target equal tokens[last] is also okay: normal non-optimized non-loop jump
                if jmp_target > tokens[last].off2int():
                    # One more weird case to look out for
                    #   if c1:
                    #      if c2:  # Jumps around the *outer* "else"
                    #       ...
                    #   else:
                    if jmp_target == tokens[last - 1].attr:
                        return False
                    if last < n and tokens[last].kind.startswith("JUMP"):
                        return False
                    return True

            pass
        pass
    return False
