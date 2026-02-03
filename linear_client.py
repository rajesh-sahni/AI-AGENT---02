"""
Linear API client – fetch issues via GraphQL.
Uses LINEAR_API_KEY from .env.
"""

import os
from typing import Any, Optional

import requests

from config import LINEAR_API_KEY, LINEAR_GRAPHQL_URL


def _headers() -> dict[str, str]:
    """Build request headers with Linear API key (no Bearer prefix for personal API keys)."""
    key = LINEAR_API_KEY or os.getenv("LINEAR_API_KEY")
    if not key:
        raise ValueError("LINEAR_API_KEY is not set in .env")
    return {
        "Authorization": key.strip(),
        "Content-Type": "application/json",
    }


def _graphql(query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Send a GraphQL request to Linear and return the JSON response."""
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(
        LINEAR_GRAPHQL_URL,
        json=payload,
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError("Linear API errors: " + str(data["errors"]))
    return data


# GraphQL query to list issues with common fields
ISSUES_LIST_QUERY = """
query ListIssues($first: Int, $after: String, $filter: IssueFilter) {
  issues(first: $first, after: $after, filter: $filter) {
    nodes {
      id
      identifier
      title
      description
      state {
        id
        name
        type
      }
      priority
      priorityLabel
      assignee {
        id
        name
        email
      }
      creator {
        id
        name
      }
      team {
        id
        name
        key
      }
      project {
        id
        name
      }
      createdAt
      updatedAt
      dueDate
      url
      labels {
        nodes {
          id
          name
          color
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

# GraphQL query to get a single issue by id or identifier
ISSUE_QUERY = """
query GetIssue($id: String) {
  issue(id: $id) {
    id
    identifier
    title
    description
    state {
      id
      name
      type
    }
    priority
    priorityLabel
    assignee {
      id
      name
      email
    }
    creator {
      id
      name
    }
    team {
      id
      name
      key
    }
    project {
      id
      name
    }
    createdAt
    updatedAt
    dueDate
    url
    labels {
      nodes {
        id
        name
        color
      }
    }
    comments {
      nodes {
        id
        body
        user { name }
        createdAt
      }
    }
  }
}
"""


def list_issues(
    first: int = 50,
    after: Optional[str] = None,
    state_filter: Optional[str] = None,
) -> dict[str, Any]:
    """
    Fetch a page of issues from Linear.

    :param first: Max number of issues (default 50).
    :param after: Cursor for pagination (from previous pageInfo.endCursor).
    :param state_filter: Optional state type: "unstarted", "started", "completed", "canceled".
    :return: Dict with "nodes" (list of issues) and "pageInfo" (hasNextPage, endCursor).
    """
    variables: dict[str, Any] = {"first": first}
    if after:
        variables["after"] = after
    if state_filter:
        variables["filter"] = {"state": {"type": state_filter}}
    data = _graphql(ISSUES_LIST_QUERY, variables)
    return data["data"]["issues"]


ISSUE_BY_IDENTIFIER_QUERY = """
query GetIssueByIdentifier($identifier: String!) {
  issues(first: 1, filter: { identifier: { eq: $identifier } }) {
    nodes {
      id
      identifier
      title
      description
      state { id name type }
      priority
      priorityLabel
      assignee { id name email }
      creator { id name }
      team { id name key }
      project { id name }
      createdAt
      updatedAt
      dueDate
      url
      labels { nodes { id name color } }
    }
  }
}
"""


def get_issue(issue_id: str) -> Optional[dict[str, Any]]:
    """
    Fetch a single issue by ID (UUID) or identifier (e.g. "PROJ-123").

    Tries issue(id) first; if not found and id looks like an identifier (XXX-NNN),
    fetches via issues(filter: { identifier: { eq: id } }).
    """
    data = _graphql(ISSUE_QUERY, {"id": issue_id})
    issue = data["data"].get("issue")
    if issue is not None:
        return issue
    # Identifier-style (e.g. PROJ-123) – fetch via filter
    if "-" in issue_id and issue_id.split("-")[-1].isdigit():
        data = _graphql(ISSUE_BY_IDENTIFIER_QUERY, {"identifier": issue_id})
        nodes = data["data"]["issues"]["nodes"]
        if nodes:
            return nodes[0]
    return None
