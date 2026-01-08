"""Tests for resume routes."""
import pytest
from fastapi import status


def test_list_resumes_empty(client):
    """Test listing resumes when database is empty."""
    response = client.get("/api/resumes")
    assert response.status_code == status.HTTP_200_OK
    assert "resumes" in response.json()
    assert response.json()["total"] == 0

