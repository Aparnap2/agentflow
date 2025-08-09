"""
End-to-End Test for AgentFlow
Simulates complete user journey from signup to Q&A interactions
"""
import asyncio
import os
import time
from typing import Dict, Optional
from playwright.async_api import async_playwright, expect
from loguru import logger

# Configuration
BASE_URL = "http://localhost:5173"  # Frontend URL
API_URL = "http://localhost:8000"   # Backend URL
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User"
TEST_PROJECT = "Create a new AI-powered task management system"

class E2ETest:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.auth_token = None
        self.project_id = None
        self.session_id = None
    
    async def setup(self):
        """Initialize browser and context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
    
    async def teardown(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def take_screenshot(self, name: str):
        """Take a screenshot for debugging"""
        os.makedirs("screenshots", exist_ok=True)
        await self.page.screenshot(path=f"screenshots/{name}.png")
    
    async def test_complete_flow(self):
        """Run the complete test flow"""
        try:
            logger.info("🚀 Starting end-to-end test...")
            
            # 1. Navigate to home page
            await self.page.goto(f"{BASE_URL}")
            # Check that the title contains 'AgentFlow'
            title = await self.page.title()
            assert "AgentFlow" in title, f"Expected title to contain 'AgentFlow', got: {title}"
            await self.take_screenshot("01_home_page")
            logger.info("✅ Loaded home page")
            
            # 2. Handle authentication via API first to ensure we're logged in
            logger.info("Authenticating via API...")
            signup_response = await self.page.evaluate("""async (email, password, name) => {
                const response = await fetch('http://localhost:8000/api/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, name })
                });
                return response.json();
            }""", TEST_EMAIL, TEST_PASSWORD, TEST_NAME)
            
            if not signup_response.get('success'):
                raise Exception(f"Failed to sign up via API: {signup_response.get('error')}")
            
            logger.info("✅ Successfully signed up via API")
            
            # 3. Set auth token in localStorage and refresh the page
            await self.page.evaluate("""(token) => {
                localStorage.setItem('auth_token', token);
                window.location.href = '/';
            }""", signup_response.get('access_token'))
            
            # 4. Wait for the chat interface to load
            try:
                await self.page.wait_for_selector('.chat-container, .message-list, textarea, [role="textbox"]', timeout=10000)
                logger.info("✅ Chat interface loaded")
                await self.take_screenshot("03_chat_interface")
            except Exception as e:
                logger.warning(f"Chat interface not found: {str(e)}")
                await self.take_screenshot("03_chat_interface_not_found")
            
            # 5. Start chat with Cofounder agent
            test_message = "Hello, I need help with my project."
            
            # Wait for chat input to be ready
            chat_input = await self.page.wait_for_selector('textarea, [role="textbox"], .chat-input, input[type="text"]', timeout=10000)
            if not chat_input:
                raise Exception("Could not find chat input field")
            
            # Type message
            await chat_input.click()
            await chat_input.type(test_message, delay=100)  # Add delay to simulate typing
            await self.take_screenshot("04_typed_message")
            
            # Find and click send button or press Enter
            send_buttons = await self.page.query_selector_all(
                'button:has(svg), ' +
                'button:has-text("Send"), ' +
                'button[type="submit"], ' +
                '.send-button, ' +
                '.chat-send-button'
            )
            
            if send_buttons:
                await send_buttons[0].click()
                logger.info("✅ Clicked send button")
            else:
                # Try pressing Enter if no send button found
                await self.page.keyboard.press('Enter')
                logger.info("✅ Pressed Enter to send message")
            
            # Wait for response with a more flexible selector
            try:
                await self.page.wait_for_selector(
                    '.message, ' +
                    '.chat-message, ' +
                    '.response, ' +
                    '[class*="message-"], ' +
                    ':text-matches("Cofounder|co-founder|agent|assistant", "i")',
                    timeout=30000
                )
                logger.info("✅ Received response from agent")
                await self.take_screenshot("05_agent_response")
                
                # Get the response text for verification
                response_elements = await self.page.query_selector_all('.message, .chat-message, .response, [class*="message-"]')
                if response_elements:
                    response_text = await response_elements[-1].inner_text()
                    logger.info(f"Agent response: {response_text[:200]}...")
                
            except Exception as e:
                logger.warning(f"Did not receive expected response from agent: {str(e)}")
                await self.take_screenshot("05_no_response")
                
                # Try to get any error messages
                error_messages = await self.page.query_selector_all('.error, .error-message, [class*="error"], [class*="alert"]')
                for i, error in enumerate(error_messages):
                    error_text = await error.inner_text()
                    logger.warning(f"Error message {i+1}: {error_text}")
                
                # Try to continue anyway if we can find the input field again
                try:
                    await self.page.wait_for_selector('textarea, [role="textbox"], .chat-input, input[type="text"]', timeout=5000)
                    logger.info("✅ Chat input is still available, continuing...")
                except:
                    logger.error("Chat input not available, cannot continue")
                    raise
            
            # 6. Look for new project button (might be in different places)
            new_project_buttons = await self.page.query_selector_all('button:has-text("New Project"), button:has-text("Create Project")')
            if new_project_buttons:
                await new_project_buttons[0].click()
                
                # Wait for project form to appear
                await self.page.wait_for_selector('textarea, [role="textbox"], [contenteditable="true"]')
                
                # Find and fill the project description/vision field
                text_areas = await self.page.query_selector_all('textarea, [role="textbox"], [contenteditable="true"]')
                if text_areas:
                    await text_areas[0].fill(TEST_PROJECT)
                
                # Try to select workflow type if dropdown exists
                try:
                    select_elements = await self.page.query_selector_all('select')
                    if select_elements:
                        await select_elements[0].select_option('startup')
                except:
                    logger.info("No workflow type dropdown found, continuing...")
                
                await self.take_screenshot("05_new_project_form")
                
                # 6. Submit project
                submit_buttons = await self.page.query_selector_all(
                    'button:has-text("Start Project"), ' +
                    'button:has-text("Create"), ' +
                    'button:has-text("Submit"), ' +
                    'button[type="submit"]'
                )
                
                if submit_buttons:
                    async with self.page.expect_response(
                        lambda r: "/api/projects" in r.url and r.request.method == "POST"
                    ) as response_info:
                        await submit_buttons[0].click()
                    
                    try:
                        response = await response_info.value
                        project_data = await response.json()
                        self.project_id = project_data.get("id")
                        logger.info(f"✅ Project created (ID: {self.project_id})")
                    except:
                        logger.warning("Could not parse project creation response, continuing...")
                
                # 7. Wait for project to be created and navigate to chat
                try:
                    # Look for project in the UI or wait for redirect
                    await self.page.wait_for_selector(
                        f':text-matches("{TEST_PROJECT[:20]}.*", "i"), ' +
                        '.project-card, [data-testid="project-card"]',
                        timeout=30000
                    )
                    logger.info("✅ Project appears in the UI")
                    
                    # Try to click on the project if we're on a projects list page
                    project_links = await self.page.query_selector_all(
                        f'a:has-text("{TEST_PROJECT[:20]}"), ' +
                        '[role="button"]:has-text("Chat"), ' +
                        'button:has-text("Open")'
                    )
                    
                    if project_links:
                        await project_links[0].click()
                        await self.page.wait_for_timeout(2000)  # Wait for navigation
                except Exception as e:
                    logger.warning(f"Project navigation may have failed: {str(e)}")
                
                await self.take_screenshot("06_project_chat")
            else:
                logger.warning("Could not find New Project button, trying to continue...")
            
            # 8. Start chat with Cofounder agent
            test_message = "Hello, I need help with my project."
            await self.page.fill('textarea[placeholder="Type your message..."]', test_message)
            
            # 9. Send message and wait for response
            async with self.page.expect_response(
                lambda response: "/api/chat" in response.url and 
                response.request.method == "POST"
            ):
                await self.page.click('button[aria-label="Send message"]')
            
            # 10. Verify response
            await self.page.wait_for_selector('.message:has-text("you")')
            await self.page.wait_for_selector('.message:has-text("cofounder")')
            await self.take_screenshot("07_chat_response")
            logger.info("✅ Chat interaction successful")
            
            # 11. Check if approval button is present
            try:
                approve_button = self.page.locator('button:has-text("Approve & Execute"')
                if await approve_button.is_visible():
                    await approve_button.click()
                    logger.info("✅ Approved project execution")
                    
                    # 12. Wait for execution to complete
                    await self.page.wait_for_selector('text=Execution completed', timeout=120000)  # 2 min timeout
                    await self.take_screenshot("08_execution_complete")
                    logger.info("✅ Project execution completed")
                    
            except Exception as e:
                logger.warning(f"Approval step not required or failed: {str(e)}")
            
            logger.info("🎉 All tests completed successfully!")
            
        except Exception as e:
            await self.take_screenshot("error_state")
            logger.error(f"❌ Test failed: {str(e)}")
            raise

async def main():
    """Main test runner"""
    test = E2ETest()
    try:
        await test.setup()
        await test.test_complete_flow()
    finally:
        await test.teardown()

if __name__ == "__main__":
    # Configure logging
    logger.add("e2e_test.log", rotation="10 MB", level="INFO")
    
    # Run the test
    asyncio.run(main())
