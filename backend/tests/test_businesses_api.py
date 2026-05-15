import asyncio
import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings

API = settings.API_PREFIX


@pytest.mark.asyncio
async def test_create_business(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/businesses",
        json={"name": "Acme Corp", "industry": "fintech"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["industry"] == "fintech"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_business_empty_name_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/businesses",
        json={"name": "   "},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_businesses_filter_by_name(client: AsyncClient) -> None:
    await client.post(f"{API}/businesses", json={"name": "Alpha Inc"})
    await client.post(f"{API}/businesses", json={"name": "Beta LLC"})

    response = await client.get(f"{API}/businesses", params={"name": "alpha"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Alpha Inc"


@pytest.mark.asyncio
async def test_get_business_detail_not_found(client: AsyncClient) -> None:
    unknown_id = uuid.uuid4()
    response = await client.get(f"{API}/businesses/{unknown_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Business not found"


@pytest.mark.asyncio
async def test_evaluate_and_complete_history(client: AsyncClient) -> None:
    create = await client.post(f"{API}/businesses", json={"name": "Risky Co"})
    business_id = create.json()["id"]

    evaluate = await client.post(f"{API}/businesses/{business_id}/evaluate")
    assert evaluate.status_code == 202
    assert evaluate.json()["status"] == "pending"

    for _ in range(20):
        history = await client.get(f"{API}/businesses/{business_id}/risk-history")
        assert history.status_code == 200
        items = history.json()["items"]
        if items and items[0]["status"] == "completed":
            assert items[0]["score"] is not None
            assert items[0]["risk_level"] in ("low", "medium", "high")
            break
        await asyncio.sleep(0.05)
    else:
        pytest.fail("evaluation did not complete in time")


@pytest.mark.asyncio
async def test_evaluate_conflict_while_active(client: AsyncClient) -> None:
    create = await client.post(f"{API}/businesses", json={"name": "Busy Co"})
    business_id = create.json()["id"]

    first = await client.post(f"{API}/businesses/{business_id}/evaluate")
    assert first.status_code == 202

    second = await client.post(f"{API}/businesses/{business_id}/evaluate")
    assert second.status_code == 409
    assert second.json()["detail"] == "Risk evaluation already in progress"


@pytest.mark.asyncio
async def test_risk_history_empty(client: AsyncClient) -> None:
    create = await client.post(f"{API}/businesses", json={"name": "New Co"})
    business_id = create.json()["id"]

    response = await client.get(f"{API}/businesses/{business_id}/risk-history")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_evaluate_not_found(client: AsyncClient) -> None:
    unknown_id = uuid.uuid4()
    response = await client.post(f"{API}/businesses/{unknown_id}/evaluate")
    assert response.status_code == 404
