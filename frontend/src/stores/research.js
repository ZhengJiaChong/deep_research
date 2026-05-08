import { defineStore } from 'pinia'
import api from '../api/research'

export const useResearchStore = defineStore('research', {
  state: () => ({
    currentResearch: null,
    researches: [],
    loading: false,
    error: null
  }),
  
  getters: {
    getCurrentResearch: (state) => state.currentResearch
  },
  
  actions: {
    async startResearch(query, selectedSkills = []) {
      this.loading = true
      this.error = null
      
      try {
        const response = await api.startResearch(query, selectedSkills)
        
        this.currentResearch = {
          id: response.research_id,
          query,
          status: response.status,
          selectedSkills
        }
        
        return response
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async getOutline(researchId) {
      try {
        const response = await api.getOutline(researchId)
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    async getProgress(researchId) {
      try {
        const response = await api.getProgress(researchId)
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    async getReport(researchId) {
      try {
        const response = await api.getReport(researchId)
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    clearCurrentResearch() {
      this.currentResearch = null
      this.error = null
    }
  }
})
