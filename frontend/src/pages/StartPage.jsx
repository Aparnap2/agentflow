import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const StartPage = () => {
  const navigate = useNavigate()
  
  useEffect(() => {
    // Redirect directly to conversation page
    navigate('/conversation')
  }, [navigate])
  
  // This component redirects to conversation, so return null
  return null
}

export default StartPage