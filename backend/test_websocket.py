"""
测试WebSocket连接
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:5611/ws"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Send bootstrap message
            bootstrap_msg = {
                "type": "bootstrap",
                "username": "default",
                "initial_capital": 10000
            }
            print(f"Sending bootstrap: {bootstrap_msg}")
            await websocket.send(json.dumps(bootstrap_msg))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"Received: {response}")
            
            data = json.loads(response)
            if data.get("type") == "bootstrap_ok":
                print("✅ Bootstrap successful!")
                print(f"   User: {data.get('user')}")
                print(f"   Account: {data.get('account')}")
            
            # Wait for snapshot
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"Received snapshot: {json.loads(response).get('type')}")
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
