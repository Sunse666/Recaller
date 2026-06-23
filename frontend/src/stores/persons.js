import { defineStore } from 'pinia'
import { api } from '../api/client'

export const usePersonsStore = defineStore('persons', {
  state: () => ({
    persons: [],
    currentPerson: null,
    currentAccount: null,
    accounts: [],
    loading: false,
  }),
  actions: {
    async fetchPersons(search = '') {
      this.loading = true
      try {
        this.persons = await api.listPersons(search)
      } finally {
        this.loading = false
      }
    },
    async fetchPerson(id) {
      this.currentPerson = await api.getPerson(id)
      return this.currentPerson
    },
    async fetchAccounts(personId) {
      this.accounts = await api.listAccounts(personId)
      if (this.accounts.length > 0 && !this.currentAccount) {
        this.currentAccount = this.accounts[0]
      }
      return this.accounts
    },
    setCurrentAccount(account) {
      this.currentAccount = account
    },
  },
})
