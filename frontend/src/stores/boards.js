import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useBoardStore = defineStore('boards', {
  state: () => ({
    boards: [],
    currentBoardId: Number(localStorage.getItem('currentBoardId')) || null,
    loading: false,
  }),
  getters: {
    currentBoard: (state) => state.boards.find(b => b.id === state.currentBoardId) || null,
    hasBoards: (state) => state.boards.length > 0,
  },
  actions: {
    async fetchBoards() {
      this.loading = true
      try {
        this.boards = await api.listBoards()
        if (!this.currentBoardId && this.boards.length > 0) {
          this.currentBoardId = this.boards[0].id
          localStorage.setItem('currentBoardId', this.currentBoardId)
        }
      } catch { this.boards = [] }
      finally { this.loading = false }
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
