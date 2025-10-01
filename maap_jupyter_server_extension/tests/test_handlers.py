import json


async def test_get_example(jp_fetch):
    # When
    response = await jp_fetch("maap-jupyter-server-extension", "test")

    # Then
    assert response.code == 200
    payload = json.loads(response.body)
    assert payload == {
        "data": "This is /maap-jupyter-server-extension/test endpoint!"
    }