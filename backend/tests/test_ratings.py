from app.schemas import SubmitRatingsRequest

def test_ratings_schema():
    payload = SubmitRatingsRequest(
        participantId="abc",
        taskId="t1",
        taskIdxInBlock=1,
        ratings=[{"slot":1,"condition":"baseline","responseId":"r1","usefulness":5,"novelty":4,"generationTimeMs":120}]
    )
    assert payload.taskIdxInBlock == 1
    assert payload.ratings[0]["slot"] == 1
