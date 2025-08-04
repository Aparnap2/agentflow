import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import AgentAvatar from './AgentAvatar'

const AgentTransition = ({ 
  fromAgent, 
  toAgent, 
  onComplete = () => {},
  message = null
}) => {
  const [stage, setStage] = useState('start')
  
  useEffect(() => {
    // Animation sequence
    const sequence = async () => {
      // Start with fromAgent
      setStage('start')
      
      // After 1s, show transition
      setTimeout(() => {
        setStage('transition')
      }, 1000)
      
      // After 2s, show toAgent
      setTimeout(() => {
        setStage('end')
      }, 2000)
      
      // After 3s, complete transition
      setTimeout(() => {
        onComplete()
      }, 3000)
    }
    
    sequence()
  }, [fromAgent, toAgent])
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-md w-full shadow-2xl">
        <div className="flex flex-col items-center">
          <AnimatePresence mode="wait">
            {stage === 'start' && (
              <motion.div
                key="fromAgent"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center"
              >
                <AgentAvatar agent={fromAgent} size="xl" />
                <h3 className="mt-4 text-xl font-semibold text-gray-900">
                  {fromAgent} Agent
                </h3>
                <p className="text-gray-600 mt-2">
                  Handing off to {toAgent} Agent...
                </p>
              </motion.div>
            )}
            
            {stage === 'transition' && (
              <motion.div
                key="transition"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.2 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center"
              >
                <div className="relative">
                  <motion.div
                    animate={{ 
                      x: [-50, 0],
                      opacity: [1, 0.5]
                    }}
                    transition={{ duration: 1, repeat: 0 }}
                    className="absolute"
                  >
                    <AgentAvatar agent={fromAgent} size="lg" />
                  </motion.div>
                  
                  <div className="mx-8 my-6">
                    <motion.div
                      animate={{ 
                        scale: [1, 1.2, 1],
                        rotate: [0, 180, 360]
                      }}
                      transition={{ duration: 1.5, repeat: 0 }}
                      className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </motion.div>
                  </div>
                  
                  <motion.div
                    animate={{ 
                      x: [50, 0],
                      opacity: [0.5, 1]
                    }}
                    transition={{ duration: 1, repeat: 0 }}
                    className="absolute"
                  >
                    <AgentAvatar agent={toAgent} size="lg" />
                  </motion.div>
                </div>
                
                <h3 className="mt-8 text-xl font-semibold text-gray-900">
                  Transitioning...
                </h3>
              </motion.div>
            )}
            
            {stage === 'end' && (
              <motion.div
                key="toAgent"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center"
              >
                <AgentAvatar agent={toAgent} size="xl" />
                <h3 className="mt-4 text-xl font-semibold text-gray-900">
                  {toAgent} Agent
                </h3>
                <p className="text-gray-600 mt-2">
                  {message || `${toAgent} Agent is now active`}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default AgentTransition