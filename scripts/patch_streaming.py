
import json
import os

def patch():
    file_path = '/Users/jmoncayopursuit.org/Desktop/Cerebrate-HOTS-War-Room/api_server.py'
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Find analyze_image start
    start_idx = -1
    for i, line in enumerate(lines):
        if "@app.route('/api/analyze_image'" in line:
            start_idx = i
            break
            
    if start_idx == -1:
        print("Could not find analyze_image start")
        return

    # Find analyze_image end (next route or health or EOF)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if "@app.route" in lines[i]:
            end_idx = i
            break

    print(f"Patching lines {start_idx+1} to {end_idx}")

    new_streaming_func = [
        "@app.route('/api/analyze_image', methods=['POST'])\n",
        "def analyze_image():\n",
        "    \"\"\"Handle multipart image uploads with multi-phase streaming.\"\"\"\n",
        "    from flask import stream_with_context, Response\n",
        "    try:\n",
        "        if 'image' not in request.files:\n",
        "            return jsonify({'error': 'No image file provided'}), 400\n",
        "        \n",
        "        image_file = request.files['image']\n",
        "        user_prompt = request.form.get('prompt', '')\n",
        "        img_bytes = image_file.read()\n",
        "        \n",
        "        import base64\n",
        "        base64_image = base64.b64encode(img_bytes).decode('utf-8')\n",
        "\n",
        "        def generate():\n",
        "            try:\n",
        "                # 1. FAST PATH: LOCAL MAP STRATEGIES\n",
        "                map_strategies = {}\n",
        "                with DB._get_connection() as conn:\n",
        "                    rows = conn.execute(\"SELECT * FROM strategies WHERE category = 'map_strategy'\").fetchall()\n",
        "                    for row in rows:\n",
        "                        try: \n",
        "                             # Try both possible column names for compatibility\n",
        "                             r_dict = dict(row)\n",
        "                             c_json = r_dict.get('content_json') or r_dict.get('strategy_json')\n",
        "                             map_strategies[r_dict.get('key') or r_dict.get('name')] = json.loads(c_json)\n",
        "                        except: continue\n",
        "\n",
        "                detected_map_fast = None\n",
        "                if user_prompt:\n",
        "                    up_low = user_prompt.lower()\n",
        "                    for m_name in map_strategies.keys():\n",
        "                        if m_name and m_name.lower() in up_low: \n",
        "                            detected_map_fast = m_name\n",
        "                            break\n",
        "                \n",
        "                # Phase 1: INSTANT MAP ASSETS\n",
        "                if detected_map_fast:\n",
        "                    s_data = map_strategies[detected_map_fast]\n",
        "                    msg = f\"## {detected_map_fast.upper()} // [DRAFT ASSETS]\\n\\n\"\n",
        "                    msg += \"### 🎯 TOP RECOMMENDATIONS\\n\"\n",
        "                    \n",
        "                    recommendations = []\n",
        "                    if isinstance(s_data, dict):\n",
        "                        if 'primary' in s_data:\n",
        "                            p = s_data['primary']\n",
        "                            recommendations.append(f\"**{p.get('name', 'Primary')}** ({p.get('global', '??')} WR) - {p.get('trigger', 'Strategic choice')}. `{p.get('code', '')}`\")\n",
        "                        if 'backups' in s_data:\n",
        "                            for b in s_data['backups'][:3]:\n",
        "                                recommendations.append(f\"**{b.get('name', 'Backup')}** ({b.get('global', '??')} WR) - {b.get('trigger', 'Solid alternative')}. `{b.get('code', '')}`\")\n",
        "                    elif isinstance(s_data, list):\n",
        "                        for item in s_data[:4]:\n",
        "                            if isinstance(item, dict):\n",
        "                                recommendations.append(f\"**{item.get('hero', item.get('name', 'Hero'))}** - {item.get('verdict', item.get('insight', 'Neural Link asset'))}\")\n",
        "                            else:\n",
        "                                recommendations.append(str(item))\n",
        "\n",
        "                    if recommendations:\n",
        "                        for r in recommendations:\n",
        "                            msg += f\"- {r}\\n\"\n",
        "                    else:\n",
        "                        msg += \"- *Retrieving specific neural links...*\\n\"\n",
        "                    \n",
        "                    msg += \"\\n*Neural Link processing... Deep analysis starting.*\"\n",
        "                    \n",
        "                    yield json.dumps({\n",
        "                        \"step\": \"fast_path\",\n",
        "                        \"analysis\": {\"direct_answer\": msg},\n",
        "                        \"link_quality\": \"Fast Cache\"\n",
        "                    }) + \"\\n\"\n",
        "\n",
        "                # 2. DEEP VISION ANALYSIS\n",
        "                player_interactions = CACHE.player_interactions or {}\n",
        "                known_players = []\n",
        "                for pid, data in list(player_interactions.items())[:20]:\n",
        "                    name = data.get('name', pid)\n",
        "                    wr_with = data.get('wins_with', 0)\n",
        "                    total_with = data.get('total_with', 0)\n",
        "                    if total_with > 0:\n",
        "                        known_players.append(f\"{name}: {wr_with}/{total_with} with\")\n",
        "                \n",
        "                social_ctx = \"\\n\\n**KNOWN PLAYERS:**\\n\" + \"\\n\".join(known_players) if known_players else \"\"\n",
        "                \n",
        "                deep_prompt = f\"Analyze this screenshot. User prompt: {user_prompt if user_prompt else 'Perform tactical scan.'}\"\n",
        "                deep_prompt += \"\\n\\nInclude Social Intelligence analysis if any player names match our database.\"\n",
        "                deep_prompt += social_ctx\n",
        "                \n",
        "                final_response = call_gemini_api(deep_prompt, None, image_data=base64_image)\n",
        "                \n",
        "                yield json.dumps({\n",
        "                    \"step\": \"deep_analysis\",\n",
        "                    \"analysis\": {\"direct_answer\": final_response},\n",
        "                    \"link_quality\": \"High Fidelity\"\n",
        "                }) + \"\\n\"\n",
        "                \n",
        "            except Exception as e:\n",
        "                yield json.dumps({\"error\": str(e)}) + \"\\n\"\n",
        "        \n",
        "        return Response(stream_with_context(generate()), mimetype='application/x-ndjson')\n",
        "        \n",
        "    except Exception as e:\n",
        "        ColoredLogger.error(f\"/api/analyze_image Exception: {e}\", \"API\")\n",
        "        return jsonify({'error': str(e)}), 500\n",
        "\n"
    ]

    final_lines = lines[:start_idx] + new_streaming_func + lines[end_idx:]
    with open(file_path, 'w') as f:
        f.writelines(final_lines)
    print("Updated analyze_image successfully.")

if __name__ == '__main__':
    patch()
