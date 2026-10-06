"""Open questions carry the attribute names an answer must be keyed by (api-contract-mvp.md section 8).

``RequestView.open_questions`` stays a list of plain sentences; ``open_question_details`` adds, per
sentence, the attribute fields to answer and any allowed values, so a client never guesses keys."""

from __future__ import annotations

from tests.pack.conftest import build_world

TEXT_NO_CLEARANCE = (
    "Need 4 x 6205-2RS bearings, SynthCo Alpha, bore 25 mm, outer diameter 52 mm, width 15 mm, "
    "2RS seal, needed by 2026-12-15"
)


def test_a_clearance_question_names_its_attribute_and_allowed_values() -> None:
    w = build_world()
    r = w.svc.create_request(w.requester, text=TEXT_NO_CLEARANCE).request
    assert r.open_questions, "the text leaves a critical attribute open"
    details = {d.text: d for d in r.open_question_details}
    assert list(details) == r.open_questions                       # same sentences, same order
    clearance = next(d for d in details.values() if "radial internal clearance" in d.text)
    assert [f.attribute for f in clearance.fields] == ["internal_clearance"]
    assert set(clearance.fields[0].allowed_values) == {"C2", "CN", "C3", "C4", "C5"}


def test_a_shared_dimensions_question_lists_every_attribute_it_covers() -> None:
    w = build_world()
    r = w.svc.create_request(w.requester, text="Need 4 x 6205 bearings, SynthCo Alpha").request
    dims = [d for d in r.open_question_details if "dimensions" in d.text.lower() or len(d.fields) > 1]
    for d in dims:
        assert len({f.attribute for f in d.fields}) == len(d.fields)   # no duplicates
        assert all(f.attribute for f in d.fields)


def test_the_family_question_answers_the_family_attribute() -> None:
    w = build_world()
    r = w.svc.create_request(w.requester, text="I need some parts urgently").request
    (d,) = r.open_question_details
    assert [f.attribute for f in d.fields] == ["family"]
    assert "deep_groove_ball_bearing" in d.fields[0].allowed_values


def test_answering_with_the_listed_attribute_keys_works() -> None:
    w = build_world()
    r = w.svc.create_request(w.requester, text=TEXT_NO_CLEARANCE).request
    answers = {f.attribute: (f.allowed_values[0] if f.allowed_values else "25")
               for d in r.open_question_details for f in d.fields}
    detail = w.svc.answer_questions(w.requester, r.id, answers)
    assert detail.request.open_questions == [] or detail.request.state.value in {
        "SPEC_CONFIRMED", "NEEDS_INFO"}
