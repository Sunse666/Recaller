const BASE = '/api'

async function request(url, options = {}) {
  const isUpload = options.headers && options.headers[''] === undefined
  const headers = isUpload ? { ...options.headers } : { 'Content-Type': 'application/json', ...options.headers }
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
  // auth
  login(username, password) {
    return request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
  },
  register(username, password) {
    return request('/auth/register', { method: 'POST', body: JSON.stringify({ username, password }) })
  },
  me() { return request('/auth/me') },
  logout() { return request('/auth/logout', { method: 'POST' }) },
  changePassword(old_password, new_password) {
    return request('/auth/change-password', { method: 'POST', body: JSON.stringify({ old_password, new_password }) })
  },

  // upload
  upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request('/upload', { method: 'POST', body: formData, headers: {} })
  },

  // users
  getUserProfile(uid) { return request(`/users/${uid}`) },

  // boards
  listBoards() { return request('/boards') },
  getDefaultBoard() { return request('/boards/default') },
  createBoard(data) { return request('/boards', { method: 'POST', body: JSON.stringify(data) }) },
  updateBoard(id, data) { return request(`/boards/${id}`, { method: 'PUT', body: JSON.stringify(data) }) },
  deleteBoard(id) { return request(`/boards/${id}`, { method: 'DELETE' }) },

  // persons
  listPersons(search = '', boardId = null) {
    let url = `/persons?search=${encodeURIComponent(search)}`
    if (boardId) url += `&board_id=${boardId}`
    return request(url)
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
  listGroups(search = '', boardId = null) {
    let url = `/groups?search=${encodeURIComponent(search)}`
    if (boardId) url += `&board_id=${boardId}`
    return request(url)
  },
  getGroup(id) { return request(`/groups/${id}`) },
  createGroup(data) { return request('/groups', { method: 'POST', body: JSON.stringify(data) }) },
  updateGroup(id, data) { return request(`/groups/${id}`, { method: 'PUT', body: JSON.stringify(data) }) },
  deleteGroup(id) { return request(`/groups/${id}`, { method: 'DELETE' }) },
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
