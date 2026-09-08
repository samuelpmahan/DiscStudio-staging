from pyto import Calculation, Part, PCR, PQL, PxC


def test_pxc_is_fail_loud_and_pql_is_composable():
    pxc = PxC()
    badges = Part("px.badges")
    remaining = Part("px.remaining.afterBadges")
    pxc.set(badges, [1, 2, 3])
    pxc.set(remaining, {10, 11})

    assert PQL.part(badges).one(pxc) == [1, 2, 3]
    assert [m.address for m in PQL.prefix("px.").where(lambda m: "badges" in m.address).matches(pxc)] == [
        "px.badges"
    ]


def test_pcr_preserves_direct_result_and_publication_semantics():
    pxc = PxC()
    source = Part("px.source")
    doubled = Part("px.doubled")
    final = Part("px.final")
    pxc.set(source, 3)

    double = Calculation("fn.double", lambda args: args["value"] * 2)
    add = Calculation("fn.add", lambda args: args["left"] + args["right"])

    pcr = PCR("demo")
    first = pcr.calc("A", double, id="double", value=source, into=doubled)
    pcr.calc("B", add, id="add", left=doubled, right=first, into=final)

    run = pcr.run(pxc)

    assert pxc.get(final) == 12
    add_testimony = run.ticks[1].calculations[0]
    assert add_testimony.inputs == {"left": "fn:double", "right": "fn:double"}


def test_duplicate_writer_rejected():
    pcr = PCR("bad")
    out = Part("px.out")
    identity = Calculation("fn.identity", lambda args: args["value"])
    source = Part("px.source")

    pcr.calc("A", identity, id="one", value=source, into=out)

    try:
        pcr.calc("B", identity, id="two", value=source, into=out)
    except ValueError as error:
        assert "multiple writers" in str(error)
    else:
        raise AssertionError("expected multiple-writer failure")
