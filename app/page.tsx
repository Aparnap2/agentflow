"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
// import { AgentMarketplace } from "@/components/sections/agent-marketplace" // Removed for now
import { EnhancedVirtualOffice } from "@/components/sections/enhanced-virtual-office"
import { LangSmithMonitoring } from "@/components/sections/langsmith-monitoring"
import { UserOnboarding } from "@/components/sections/user-onboarding"
import { Network, Users, Monitor, Settings, BarChart3, Plus, Activity, Briefcase } from "lucide-react"
import { NewTaskForm } from "@/components/forms/new-task-form" // Import the new form

export default function AgentFlowPro() {
  const [activeTab, setActiveTab] = useState("virtual-office")
  const [isOnboarded, setIsOnboarded] = useState(true) // Set to false for onboarding

  // Show onboarding for new users
  if (!isOnboarded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <header className="border-b bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Network className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    AgentFlow Pro
                  </h1>
                  <p className="text-sm text-muted-foreground">Virtual Office Setup</p>
                </div>
              </div>
              <Button variant="outline" onClick={() => setIsOnboarded(true)}>
                Skip Setup
              </Button>
            </div>
          </div>
        </header>

        <div className="container mx-auto px-4 py-8">
          <UserOnboarding />
          <div className="text-center mt-8">
            <Button onClick={() => setIsOnboarded(true)} className="bg-gradient-to-r from-blue-600 to-purple-600">
              Enter Virtual Office
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <Network className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  AgentFlow Pro
                </h1>
                <p className="text-sm text-muted-foreground">Virtual Office & AI Team Management</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 px-3 py-1">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>4 Team Members
              </Badge>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 px-3 py-1">
                <Activity className="w-3 h-3 mr-1" />8 Active Tasks
              </Badge>
              <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 px-3 py-1">
                <BarChart3 className="w-3 h-3 mr-1" />
                94% Success Rate
              </Badge>
              {/* Replace static button with the NewTaskForm component */}
              <NewTaskForm />
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white dark:bg-slate-800 shadow-sm">
            <TabsTrigger value="virtual-office" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Virtual Office
            </TabsTrigger>
            <TabsTrigger value="monitoring" className="flex items-center gap-2">
              <Monitor className="w-4 h-4" />
              Live Monitoring
            </TabsTrigger>
            {/* <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Analytics
            </TabsTrigger> */}
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Virtual Office */}
          <TabsContent value="virtual-office">
            <EnhancedVirtualOffice />
          </TabsContent>

          {/* Live Monitoring - LangSmith Style */}
          <TabsContent value="monitoring">
            <LangSmithMonitoring />
          </TabsContent>

          {/* Analytics - Removed for now, was a placeholder */}
          {/* <TabsContent value="analytics">
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold">Analytics & Performance</h2>
                <p className="text-muted-foreground">Track your virtual team's performance and business outcomes</p>
              </div>
              <div className="text-center py-12">
                <p className="text-muted-foreground">Advanced analytics dashboard coming soon...</p>
              </div>
            </div>
          </TabsContent>

          {/* Settings */}
          <TabsContent value="settings">
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold">System Settings</h2>
                <p className="text-muted-foreground">Configure your AgentFlow Pro virtual office</p>
              </div>
              <div className="text-center py-12">
                <p className="text-muted-foreground">Settings interface coming soon...</p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
