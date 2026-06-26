const BASE = '/api'

async function request(url, options = {}) {
  const isUpload = options.body instanceof FormData
  const headers = isUpload ? {} : { 'Content-Type': 'application/json', ...options.headers }
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
  loginByCode(email, code) {
    return request('/auth/login-by-code', { method: 'POST', body: JSON.stringify({ email, code }) })
  },
  sendCode(email) {
    return request('/auth/send-code', { method: 'POST', body: JSON.stringify({ email }) })
  },
  sendLoginCode(email) {
    return request('/auth/send-login-code', { method: 'POST', body: JSON.stringify({ email }) })
  },
  registerEmail(email, code, username, password) {
    return request('/auth/register-email', { method: 'POST', body: JSON.stringify({ email, code, username, password }) })
  },
  register(username, password) {
    return request('/auth/register', { method: 'POST', body: JSON.stringify({ username, password }) })
  },
  me() { return request('/auth/me') },
  logout() { return request('/auth/logout', { method: 'POST' }) },
  sendPwdCode() {
    return request('/auth/send-pwd-code', { method: 'POST' })
  },
  changePassword(old_password, new_password, code = null) {
    return request('/auth/change-password', { method: 'POST', body: JSON.stringify({ old_password, new_password, code }) })
  },
  changeEmail(email, code) {
    return request('/auth/change-email', { method: 'POST', body: JSON.stringify({ email, code }) })
  },
  changeUsername(username) {
    return request('/auth/change-username', { method: 'POST', body: JSON.stringify({ username }) })
  },
  uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request('/auth/avatar', { method: 'POST', body: formData, headers: {} })
  },

  // upload
  upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request('/upload', { method: 'POST', body: formData, headers: {} })
  },

  // images
  listImages(page = 1, pageSize = 50) { return request(`/images?page=${page}&page_size=${pageSize}`) },

  // users
  getUserProfile(uid) { return request(`/users/${uid}`) },

  // boards
  listBoards(uid = null) {
    const params = uid ? `?uid=${uid}` : ''
    return request(`/boards${params}`)
  },
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

  // relations & meetings
  listRelations(personId) { return request(`/persons/${personId}/relations`) },
  addRelation(personId, data) { return request(`/persons/${personId}/relations`, { method: 'POST', body: JSON.stringify(data) }) },
  deleteRelation(personId, relationId) { return request(`/persons/${personId}/relations/${relationId}`, { method: 'DELETE' }) },
  listMeetings(personId) { return request(`/persons/${personId}/meetings`) },
  addMeeting(personId, data) { return request(`/persons/${personId}/meetings`, { method: 'POST', body: JSON.stringify(data) }) },
  deleteMeeting(personId, meetingId) { return request(`/persons/${personId}/meetings/${meetingId}`, { method: 'DELETE' }) },

  // admin: users
  adminListUsers(params = {}) { return request(`/admin/users?${new URLSearchParams(params)}`) },
  adminCreateUser(data) { return request('/admin/users', { method: 'POST', body: JSON.stringify(data) }) },
  adminUpdateUser(uid, data) { return request(`/admin/users/${uid}`, { method: 'PUT', body: JSON.stringify(data) }) },
  adminDeleteUser(uid) { return request(`/admin/users/${uid}`, { method: 'DELETE' }) },
  adminResetPassword(uid) { return request(`/admin/users/${uid}/reset-password`, { method: 'POST' }) },
  adminForceLogout(uid) { return request(`/admin/users/${uid}/force-logout`, { method: 'POST' }) },

  // admin: dashboard
  adminDashboard() { return request('/admin/dashboard') },

  // admin: audit logs
  adminAuditLogs(params = {}) { return request(`/admin/audit-logs?${new URLSearchParams(params)}`) },

  // admin: config
  adminGetConfig() { return request('/admin/config') },
  adminUpdateConfig(data) { return request('/admin/config', { method: 'PUT', body: JSON.stringify(data) }) },

  // public config
  getPublicConfig() { return request('/public/config') },
}
