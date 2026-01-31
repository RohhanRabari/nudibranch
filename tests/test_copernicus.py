"""Tests for Copernicus Marine client."""

import pytest

from nudibranch.clients.copernicus import CopernicusClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client can be initialized."""
    client = CopernicusClient(username="test_user", password="test_pass")
    assert client.username == "test_user"
    assert client.password == "test_pass"


@pytest.mark.asyncio
async def test_fetch_turbidity_no_credentials():
    """Test fetching turbidity without credentials returns None."""
    client = CopernicusClient()
    result = await client.fetch_turbidity(7.6, 98.37)

    # Without credentials/implementation, should return None
    assert result is None


@pytest.mark.asyncio
async def test_fetch_turbidity_with_days_back():
    """Test fetching with different lookback periods."""
    client = CopernicusClient(username="test", password="test")

    # Should not crash with different days_back values
    result1 = await client.fetch_turbidity(7.6, 98.37, days_back=3)
    result2 = await client.fetch_turbidity(7.6, 98.37, days_back=7)
    result3 = await client.fetch_turbidity(7.6, 98.37, days_back=14)

    # All should return None (no actual implementation yet)
    assert result1 is None
    assert result2 is None
    assert result3 is None


@pytest.mark.asyncio
async def test_close():
    """Test client close method."""
    client = CopernicusClient()
    await client.close()  # Should not raise any errors


@pytest.mark.asyncio
async def test_dataset_configuration():
    """Test that dataset configuration is set."""
    assert CopernicusClient.DATASET_ID is not None
    assert CopernicusClient.VARIABLE_NAME is not None
    assert "cmems" in CopernicusClient.DATASET_ID.lower()
