"use client"

import { useState, FormEvent } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast" // Assuming a toast hook exists for notifications

interface NewTaskFormProps {
  onTaskCreate?: (taskId: string) => void // Callback after successful task creation
}

export function NewTaskForm({ onTaskCreate }: NewTaskFormProps) {
  const [intent, setIntent] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const { toast } = useToast() // For showing success/error messages

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!intent.trim()) {
      toast({
        title: "Error",
        description: "Please describe the task or goal.",
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)
    try {
      // TODO: Replace with actual API base URL from config or env variable
      const response = await fetch("http://localhost:8000/api/workflows", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_intent: intent,
          name: `User Task: ${intent.substring(0, 30)}${intent.length > 30 ? "..." : ""}`, // Example name
          description: intent, // Full intent can also be the description
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail || `Failed to create task: ${response.status} ${response.statusText}`
        )
      }

      const result = await response.json()
      // Backend returns: { message, workflow_id (definition_id), run_details (actual run output from orchestrator) }
      // The orchestrator.run_workflow directly returns a dict that includes 'thread_id'.
      // So, result.run_details should be that dict.
      const runDetails = result.run_details;
      const instanceId = runDetails?.thread_id || result.workflow_id; // Fallback to definition_id (workflow_id) if thread_id isn't in run_details for some reason

      toast({
        title: "Task Submitted",
        description: `Task processing initiated. Tracking ID: ${instanceId}`,
      })
      setIntent("") // Clear the form
      setIsOpen(false) // Close the dialog

      if (onTaskCreate && instanceId) {
        // Pass the instanceId if it's what we need to track, or adjust if
        // onTaskCreate expects something else (e.g. the static workflow_id for now)
        onTaskCreate(instanceId)
      }

    } catch (error) {
      console.error("Error creating task:", error)
      toast({
        title: "Error Creating Task",
        description: error instanceof Error ? error.message : "An unknown error occurred.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="bg-gradient-to-r from-blue-600 to-purple-600">
          {/* Using Plus from lucide-react, assuming it's available in parent context or passed as prop */}
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-4 w-4"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          New Task
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Create New Task / Define Goal</DialogTitle>
          <DialogDescription>
            Describe the task or overall goal you want your virtual office team to achieve.
            The Co-Founder and Manager agents will break this down into actionable steps.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-1 items-center gap-4">
              <Label htmlFor="intent-description" className="sr-only">
                Task Description
              </Label>
              <Textarea
                id="intent-description"
                placeholder="e.g., 'Launch a marketing campaign for our new product X focusing on Q3 goals.' or 'Generate monthly sales reports and identify top 3 performing regions.'"
                value={intent}
                onChange={(e) => setIntent(e.target.value)}
                className="min-h-[100px]"
                required
              />
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isSubmitting || !intent.trim()}>
              {isSubmitting ? "Submitting..." : "Submit Task"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
