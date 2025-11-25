"""
Test if AFC can be properly disabled
"""
import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

async def test_afc_disable():
    """Test AFC disable configuration"""
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Define a simple function
    test_function = types.FunctionDeclaration(
        name="extract_name",
        description="Extract the child's name from the message",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The child's name"
                }
            },
            "required": ["name"]
        }
    )

    tools = [types.Tool(function_declarations=[test_function])]

    # Test 1: Without AFC disable (should see "AFC is enabled" log)
    print("=" * 80)
    print("TEST 1: WITHOUT AFC disable (default)")
    print("=" * 80)

    config1 = types.GenerateContentConfig(
        tools=tools,
        temperature=0.0,
        max_output_tokens=500
    )

    print(f"Config 1:")
    print(f"  tools: {len(config1.tools) if config1.tools else 0}")
    print(f"  automatic_function_calling: {config1.automatic_function_calling}")
    print()

    try:
        response1 = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents="My son Danny is 3 years old",
            config=config1
        )
        print(f"Response 1: Got {len(response1.candidates[0].content.parts if response1.candidates else 0)} parts")
        if response1.candidates:
            for i, part in enumerate(response1.candidates[0].content.parts):
                if hasattr(part, 'function_call'):
                    print(f"  Part {i}: FUNCTION CALL - {part.function_call.name}")
                if hasattr(part, 'text'):
                    print(f"  Part {i}: TEXT - {part.text[:50] if part.text else 'None'}...")
    except Exception as e:
        print(f"Error: {e}")

    print()

    # Test 2: With AFC disable
    print("=" * 80)
    print("TEST 2: WITH AFC disable = True")
    print("=" * 80)

    config2 = types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        temperature=0.0,
        max_output_tokens=500
    )

    print(f"Config 2:")
    print(f"  tools: {len(config2.tools) if config2.tools else 0}")
    print(f"  automatic_function_calling: {config2.automatic_function_calling}")
    print(f"  automatic_function_calling.disable: {config2.automatic_function_calling.disable if config2.automatic_function_calling else None}")
    print()

    try:
        response2 = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents="My son Danny is 3 years old",
            config=config2
        )
        print(f"Response 2: Got {len(response2.candidates[0].content.parts if response2.candidates else 0)} parts")
        if response2.candidates:
            for i, part in enumerate(response2.candidates[0].content.parts):
                if hasattr(part, 'function_call'):
                    print(f"  Part {i}: FUNCTION CALL - {part.function_call.name}")
                    print(f"    Args: {dict(part.function_call.args)}")
                if hasattr(part, 'text'):
                    print(f"  Part {i}: TEXT - {part.text[:50] if part.text else 'None'}...")
    except Exception as e:
        print(f"Error: {e}")

    print()

    # Test 3: With mode=ANY
    print("=" * 80)
    print("TEST 3: WITH mode=ANY + AFC disable")
    print("=" * 80)

    config3 = types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY
            )
        ),
        temperature=0.0,
        max_output_tokens=500
    )

    print(f"Config 3:")
    print(f"  tools: {len(config3.tools) if config3.tools else 0}")
    print(f"  automatic_function_calling.disable: {config3.automatic_function_calling.disable if config3.automatic_function_calling else None}")
    print(f"  tool_config: {config3.tool_config}")
    print(f"  tool_config.function_calling_config.mode: {config3.tool_config.function_calling_config.mode if config3.tool_config and config3.tool_config.function_calling_config else None}")
    print()

    try:
        response3 = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents="My son Danny is 3 years old",
            config=config3
        )
        print(f"Response 3: Got {len(response3.candidates[0].content.parts if response3.candidates else 0)} parts")
        if response3.candidates:
            for i, part in enumerate(response3.candidates[0].content.parts):
                if hasattr(part, 'function_call'):
                    print(f"  Part {i}: FUNCTION CALL - {part.function_call.name}")
                    print(f"    Args: {dict(part.function_call.args)}")
                if hasattr(part, 'text'):
                    print(f"  Part {i}: TEXT - {part.text[:50] if part.text else 'None'}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_afc_disable())
