"""
WebSocket连接测试脚本
用于调试前端连接问题
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:5611/ws"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # 发送bootstrap消息
            bootstrap_msg = {
                "type": "bootstrap",
                "username": "test-user",
                "initial_capital": 10000
            }
            print(f"📤 Sending: {json.dumps(bootstrap_msg, indent=2)}")
            await websocket.send(json.dumps(bootstrap_msg))
            
            # 接收响应
            print("📥 Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"✅ Received: {response}")
            
            msg = json.loads(response)
            if msg.get("type") == "bootstrap_ok":
                print("🎉 Bootstrap successful!")
                print(f"   User: {msg.get('user')}")
                print(f"   Account: {msg.get('account')}")
                
                # 请求snapshot
                snapshot_msg = {"type": "get_snapshot"}
                print(f"\n📤 Sending: {json.dumps(snapshot_msg)}")
                await websocket.send(json.dumps(snapshot_msg))
                
                # 接收snapshot
                print("📥 Waiting for snapshot...")
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received snapshot (first 500 chars):")
                print(response[:500])
                
                print("\n✅ WebSocket test passed!")
            else:
                print(f"❌ Unexpected message type: {msg.get('type')}")
                
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 80)
    print("WebSocket连接测试")
    print("=" * 80)
    asyncio.run(test_websocket())
