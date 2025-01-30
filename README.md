# add running simulation using apis of each service and proper logs


C# code to come:

```using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using NativeWebSocket;
using Newtonsoft.Json;

public class NetworkManager : MonoBehaviour
{
    private WebSocket websocket;
    private string playerId;
    private Dictionary<string, GameObject> players = new Dictionary<string, GameObject>();
    public GameObject playerPrefab;

    private async void Start()
    {
        websocket = new WebSocket("ws://localhost:8765");

        websocket.OnOpen += () =>
        {
            Debug.Log("Connection open!");
        };

        websocket.OnError += (e) =>
        {
            Debug.LogError($"Error! {e}");
        };

        websocket.OnClose += (e) =>
        {
            Debug.Log("Connection closed!");
        };

        websocket.OnMessage += (bytes) =>
        {
            var message = System.Text.Encoding.UTF8.GetString(bytes);
            HandleMessage(message);
        };

        await websocket.Connect();
    }

    void HandleMessage(string jsonMessage)
    {
        var message = JsonConvert.DeserializeObject<Dictionary<string, object>>(jsonMessage);
        string messageType = message["type"].ToString();

        switch (messageType)
        {
            case "connection_established":
                playerId = message["player_id"].ToString();
                var gameState = JsonConvert.DeserializeObject<Dictionary<string, object>>(
                    message["game_state"].ToString());
                InitializeGameState(gameState);
                break;

            case "position_update":
                UpdatePlayerPosition(
                    message["player_id"].ToString(),
                    JsonConvert.DeserializeObject<Vector3>(message["position"].ToString())
                );
                break;

            case "game_event":
                HandleGameEvent(message["event_data"]);
                break;

            case "game_tick":
                // Handle game tick if needed
                break;
        }
    }

    void InitializeGameState(Dictionary<string, object> gameState)
    {
        var players = JsonConvert.DeserializeObject<Dictionary<string, object>>(
            gameState["players"].ToString());

        foreach (var player in players)
        {
            string id = player.Key;
            if (!this.players.ContainsKey(id))
            {
                var playerObj = Instantiate(playerPrefab, Vector3.zero, Quaternion.identity);
                this.players[id] = playerObj;
            }
        }
    }

    void UpdatePlayerPosition(string playerId, Vector3 position)
    {
        if (players.ContainsKey(playerId))
        {
            players[playerId].transform.position = position;
        }
    }

    void HandleGameEvent(object eventData)
    {
        // Handle different types of game events
        Debug.Log($"Game event received: {eventData}");
    }

    public async void SendPosition(Vector3 position)
    {
        if (websocket.State == WebSocketState.Open)
        {
            var message = new Dictionary<string, object>
            {
                { "command", "update_position" },
                { "player_id", playerId },
                { "position", new Dictionary<string, float>
                    {
                        { "x", position.x },
                        { "y", position.y },
                        { "z", position.z }
                    }
                }
            };

            await websocket.SendText(JsonConvert.SerializeObject(message));
        }
    }

    private async void Update()
    {
        if (websocket.State == WebSocketState.Open)
        {
            // Send local player position updates
            if (players.ContainsKey(playerId))
            {
                SendPosition(players[playerId].transform.position);
            }
        }

        #if !UNITY_WEBGL || UNITY_EDITOR
        websocket.DispatchMessageQueue();
        #endif
    }

    private async void OnApplicationQuit()
    {
        await websocket.Close();
    }
}```
