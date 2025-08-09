import { useState, useEffect } from 'react'
import { Users, TrendingUp, DollarSign, Activity, Plus } from 'lucide-react'
import prdApi from '../../lib/prd-api'

const HubSpotPanel = () => {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('contacts')
  const [showCreateForm, setShowCreateForm] = useState(false)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      const data = await prdApi.getPipelineAnalytics()
      setAnalytics(data)
    } catch (error) {
      console.error('Failed to fetch HubSpot analytics:', error)
    }
  }

  const createContact = async (contactData) => {
    setLoading(true)
    try {
      const result = await prdApi.createContact(contactData)
      console.log('Contact created successfully')
      setShowCreateForm(false)
      // Refresh contacts list if needed
      return result
    } catch (error) {
      console.error('Failed to create contact:', error)
      return { error: error.message }
    } finally {
      setLoading(false)
    }
  }

  const createDeal = async (dealData) => {
    setLoading(true)
    try {
      const result = await prdApi.createDeal(dealData)
      console.log('Deal created successfully')
      setShowCreateForm(false)
      // Refresh deals list if needed
      return result
    } catch (error) {
      console.error('Failed to create deal:', error)
      return { error: error.message }
    } finally {
      setLoading(false)
    }
  }



  const AnalyticsDashboard = () => {
    if (!analytics) return null

    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Deals</p>
              <p className="text-2xl font-semibold text-gray-900">
                {analytics.total_deals || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Value</p>
              <p className="text-2xl font-semibold text-gray-900">
                ${(analytics.total_value || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Avg Deal Size</p>
              <p className="text-2xl font-semibold text-gray-900">
                ${(analytics.average_deal_size || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-orange-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Pipeline Health</p>
              <p className="text-2xl font-semibold text-gray-900">
                {analytics.total_deals > 0 ? 'Good' : 'No Data'}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const CreateContactForm = () => {
    const [formData, setFormData] = useState({
      email: '',
      firstname: '',
      lastname: '',
      company: '',
      phone: ''
    })

    const handleSubmit = async (e) => {
      e.preventDefault()
      if (formData.email) {
        await createContact(formData)
        setFormData({
          email: '',
          firstname: '',
          lastname: '',
          company: '',
          phone: ''
        })
      }
    }

    return (
      <div className="bg-white rounded-lg border p-4 mb-4">
        <h3 className="font-semibold text-gray-900 mb-3">Create New Contact</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              type="email"
              placeholder="Email *"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({...prev, email: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
              required
            />
            <input
              type="text"
              placeholder="Company"
              value={formData.company}
              onChange={(e) => setFormData(prev => ({...prev, company: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="First Name"
              value={formData.firstname}
              onChange={(e) => setFormData(prev => ({...prev, firstname: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
            />
            <input
              type="text"
              placeholder="Last Name"
              value={formData.lastname}
              onChange={(e) => setFormData(prev => ({...prev, lastname: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
            />
          </div>

          <input
            type="tel"
            placeholder="Phone"
            value={formData.phone}
            onChange={(e) => setFormData(prev => ({...prev, phone: e.target.value}))}
            className="w-full px-3 py-2 border rounded-md text-sm"
          />
          
          <div className="flex space-x-2">
            <button
              type="submit"
              disabled={loading || !formData.email}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              {loading ? 'Creating...' : 'Create Contact'}
            </button>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    )
  }

  const CreateDealForm = () => {
    const [formData, setFormData] = useState({
      dealname: '',
      amount: '',
      dealstage: 'appointmentscheduled',
      contact_email: ''
    })

    const handleSubmit = async (e) => {
      e.preventDefault()
      if (formData.dealname && formData.dealstage) {
        const dealData = {
          ...formData,
          amount: formData.amount ? parseFloat(formData.amount) : null
        }
        await createDeal(dealData)
        setFormData({
          dealname: '',
          amount: '',
          dealstage: 'appointmentscheduled',
          contact_email: ''
        })
      }
    }

    return (
      <div className="bg-white rounded-lg border p-4 mb-4">
        <h3 className="font-semibold text-gray-900 mb-3">Create New Deal</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Deal Name *"
              value={formData.dealname}
              onChange={(e) => setFormData(prev => ({...prev, dealname: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
              required
            />
            <input
              type="number"
              placeholder="Amount"
              value={formData.amount}
              onChange={(e) => setFormData(prev => ({...prev, amount: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <select
              value={formData.dealstage}
              onChange={(e) => setFormData(prev => ({...prev, dealstage: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
              required
            >
              <option value="appointmentscheduled">Appointment Scheduled</option>
              <option value="qualifiedtobuy">Qualified to Buy</option>
              <option value="presentationscheduled">Presentation Scheduled</option>
              <option value="decisionmakerboughtin">Decision Maker Bought-In</option>
              <option value="contractsent">Contract Sent</option>
              <option value="closedwon">Closed Won</option>
              <option value="closedlost">Closed Lost</option>
            </select>
            <input
              type="email"
              placeholder="Contact Email (optional)"
              value={formData.contact_email}
              onChange={(e) => setFormData(prev => ({...prev, contact_email: e.target.value}))}
              className="px-3 py-2 border rounded-md text-sm"
            />
          </div>
          
          <div className="flex space-x-2">
            <button
              type="submit"
              disabled={loading || !formData.dealname}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm"
            >
              {loading ? 'Creating...' : 'Create Deal'}
            </button>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    )
  }

  const StageBreakdown = () => {
    if (!analytics?.stage_breakdown) return null

    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Breakdown</h3>
        
        <div className="space-y-3">
          {Object.entries(analytics.stage_breakdown).map(([stage, data]) => (
            <div key={stage} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <h4 className="font-medium text-gray-900">
                  {stage.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </h4>
                <p className="text-sm text-gray-600">{data.count} deals</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-gray-900">
                  ${data.value.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">
                  Avg: ${data.count > 0 ? (data.value / data.count).toLocaleString() : '0'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-orange-600" />
          <h2 className="text-lg font-semibold text-gray-900">HubSpot CRM</h2>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchAnalytics}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
          >
            Refresh
          </button>
          
          {!showCreateForm && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              <Plus className="h-4 w-4" />
              <span>Create</span>
            </button>
          )}
        </div>
      </div>

      <AnalyticsDashboard />

      {showCreateForm && (
        <div className="mb-6">
          <div className="flex space-x-2 mb-4">
            <button
              onClick={() => setActiveTab('contacts')}
              className={`px-4 py-2 rounded-md text-sm ${
                activeTab === 'contacts' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Contact
            </button>
            <button
              onClick={() => setActiveTab('deals')}
              className={`px-4 py-2 rounded-md text-sm ${
                activeTab === 'deals' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Deal
            </button>
          </div>

          {activeTab === 'contacts' ? <CreateContactForm /> : <CreateDealForm />}
        </div>
      )}

      <StageBreakdown />
    </div>
  )
}

export default HubSpotPanel