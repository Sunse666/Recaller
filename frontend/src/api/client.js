const BASE = '/api'

async function request(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const res = await fetch(`${BASE}${url}`, {
    headers,
    credentials: 'same-origin',
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // persons
  listPersons(search = '') {
    return request(`/persons?search=${encodeURIComponent(search)}`)
  },
  getPerson(id) { return request(`/persons/${id}`) },
  createPerson(data) { return request('/persons', { method: 'POST', body: JSON.stringify(data) }) },
  updatePerson(id, data) { return request(`/persons/${id}`, { method: 'PUT', body: JSON.stringify(data) }) },
  deletePerson(id) { return request(`/persons/${id}`, { method: 'DELETE' }) },

  // accounts
  listAccounts(personId) { return request(`/persons/${personId}/accounts`) },
  createAccount(personId, data) { return request(`/persons/${personId}/accounts`, { method: 'POST', body: JSON.stringify(data) }) },
  updateAccount(personId, accountId, data) { return request(`/persons/${personId}/accounts/${accountId}`, { method: 'PUT', body: JSON.stringify(data) }) },
  deleteAccount(personId, accountId) { return request(`/persons/${personId}/accounts/${accountId}`, { method: 'DELETE' }) },
  addNicknameHistory(personId, accountId, data) { return request(`/persons/${personId}/accounts/${accountId}/nicknames`, { method: 'POST', body: JSON.stringify(data) }) },
  deleteNicknameHistory(personId, accountId, historyId) { return request(`/persons/${personId}/accounts/${accountId}/nicknames/${historyId}`, { method: 'DELETE' }) },
  listMemberships(personId, accountId) { return request(`/persons/${personId}/accounts/${accountId}/memberships`) },
  updateMembership(groupId, membershipId, data) { return request(`/groups/${groupId}/members/${membershipId}`, { method: 'PUT', body: JSON.stringify(data) }) },

  // groups
  listGroups(search = '') { return request(`/groups?search=${encodeURIComponent(search)}`) },
  getGroup(id) { return request(`/groups/${id}`) },
  createGroup(data) { return request('/groups', { method: 'POST', body: JSON.stringify(data) }) },
  getGroupMembers(groupId) { return request(`/groups/${groupId}/members`) },
  addGroupMember(groupId, data) { return request(`/groups/${groupId}/members`, { method: 'POST', body: JSON.stringify(data) }) },
  updateGroupMember(groupId, membershipId, data) { return request(`/groups/${groupId}/members/${membershipId}`, { method: 'PUT', body: JSON.stringify(data) }) },
  removeGroupMember(groupId, membershipId) { return request(`/groups/${groupId}/members/${membershipId}`, { method: 'DELETE' }) },

  // relations & meetings
  listRelations(personId) { return request(`/persons/${personId}/relations`) },
  addRelation(personId, data) { return request(`/persons/${personId}/relations`, { method: 'POST', body: JSON.stringify(data) }) },
  deleteRelation(personId, relationId) { return request(`/persons/${personId}/relations/${relationId}`, { method: 'DELETE' }) },
  listMeetings(personId) { return request(`/persons/${personId}/meetings`) },
  addMeeting(personId, data) { return request(`/persons/${personId}/meetings`, { method: 'POST', body: JSON.stringify(data) }) },
  deleteMeeting(personId, meetingId) { return request(`/persons/${personId}/meetings/${meetingId}`, { method: 'DELETE' }) },
}
