import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useBoardStore = defineStore('boards', {
  state: () => ({
    boards: [],
    currentBoardId: Number(localStorage.getItem('currentBoardId')) || null,
    loading: false,
    targetUid: null,
    ownBoardId: null,
  }),
  getters: {
    currentBoard: (state) => state.boards.find(b => b.id === state.currentBoardId) || null,
    hasBoards: (state) => state.boards.length > 0,
    viewingOtherUser: (state) => state.targetUid !== null,
  },
  actions: {
    async fetchBoards(uid = null) {
      this.loading = true
      this.targetUid = uid || null
      const prevBoardId = this.currentBoardId
      try {
        this.boards = await api.listBoards(uid || null)
        if (prevBoardId && this.boards.some(b => b.id === prevBoardId)) {
          this.currentBoardId = prevBoardId
        } else if (this.boards.length > 0) {
          this.currentBoardId = this.boards[0].id
        }
      } catch { this.boards = [] }
      finally { this.loading = false }
    },
    async fetchOwnBoards() {
      this.targetUid = null
      await this.fetchBoards(null)
    },
    setCurrentBoard(boardId) {
      this.currentBoardId = boardId
      localStorage.setItem('currentBoardId', boardId)
    },
    async createBoard(data) {
      const board = await api.createBoard(data)
      this.boards.push(board)
      if (this.boards.length === 1) {
        this.setCurrentBoard(board.id)
      }
      return board
    },
    async updateBoard(id, data) {
      const updated = await api.updateBoard(id, data)
      const idx = this.boards.findIndex(b => b.id === id)
      if (idx >= 0) this.boards[idx] = updated
      return updated
    },
    async deleteBoard(id) {
      await api.deleteBoard(id)
      this.boards = this.boards.filter(b => b.id !== id)
      if (this.currentBoardId === id && this.boards.length > 0) {
        this.setCurrentBoard(this.boards[0].id)
      }
    },
  },
})
