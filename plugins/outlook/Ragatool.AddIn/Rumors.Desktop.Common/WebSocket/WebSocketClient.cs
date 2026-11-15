using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Rumors.Desktop.Common.WebSocket
{
    public class WebSocketClient : IDisposable
    {
        private readonly string _url;
        private readonly IReadOnlyList<string> _subProtocols;
        private ClientWebSocket _socket;
        private CancellationTokenSource _cts;
        private readonly ILogger _logger;

        public event Action OnOpen = delegate { };  
        public event Action<string> OnMessage = delegate { };
        public event Action OnClose = delegate { };
        public event Action<Exception> OnError = delegate { };

        public bool Connected { get; private set; }

        public WebSocketClient(string url, IEnumerable<string> subProtocols = null, ILogger logger = null)
        {
            _url = url;
            _subProtocols = subProtocols is null ? null : new List<string>(subProtocols);
            _logger = logger;
        }

        public async Task Connect()
        {
            try
            {
                _socket = new ClientWebSocket();
                _cts = new CancellationTokenSource();

                if (_subProtocols != null)
                {
                    foreach (var protocol in _subProtocols)
                    {
                        _socket.Options.AddSubProtocol(protocol);
                    }
                }

                await _socket.ConnectAsync(new Uri(_url), _cts.Token);

                OnOpen?.Invoke();

                _ = Task.Run(ReceiveLoop, _cts.Token);

                Connected = true;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Failed to connect to WebSocket at {Url}", _url);
                Connected = false;
                OnError?.Invoke(ex);
                throw;
            }
        }

        private async Task ReceiveLoop()
        {
            var buffer = new byte[1024 * 4];

            try
            {
                while (_socket != null && _socket.State == WebSocketState.Open && !_cts.IsCancellationRequested)
                {
                    using (var ms = new MemoryStream())
                    {
                        WebSocketReceiveResult result;
                        do
                        {
                            result = await _socket.ReceiveAsync(new ArraySegment<byte>(buffer), _cts.Token);
                            if (result.MessageType == WebSocketMessageType.Close)
                            {
                                await _socket.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, _cts.Token);
                                OnClose?.Invoke();
                                return;
                            }
                            ms.Write(buffer, 0, result.Count);
                        } while (!result.EndOfMessage);

                        ms.Seek(0, SeekOrigin.Begin);
                        using (var reader = new StreamReader(ms, Encoding.UTF8))
                        {
                            var message = await reader.ReadToEndAsync();
                            OnMessage?.Invoke(message);
                        }
                    }
                }
            }
            catch (OperationCanceledException)
            {
                Connected = false;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Error in WebSocket receive loop for {Url}", _url);
                Connected = false;
                OnError?.Invoke(ex);
            }
            finally
            {
                if (_socket != null && _socket.State != WebSocketState.Closed && _socket.State != WebSocketState.Aborted)
                {
                    Connected = false;
                    OnClose?.Invoke();
                }
            }
        }

        public async Task Send(string data)
        {
            if (_socket != null && _socket.State == WebSocketState.Open)
            {
                var buffer = Encoding.UTF8.GetBytes(data);
                await _socket.SendAsync(new ArraySegment<byte>(buffer), WebSocketMessageType.Text, true, _cts.Token);
            }
            else
            {
                _logger?.LogWarning("WebSocket is not connected. Cannot send data.");
                Console.Error.WriteLine("WebSocket is not connected.");
            }
        }

        public async Task Disconnect()
        {
            if (_socket != null)
            {
                _cts?.Cancel();
                if (_socket.State == WebSocketState.Open || _socket.State == WebSocketState.CloseReceived)
                {
                    try
                    {
                        await _socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Disconnecting", CancellationToken.None);
                    }
                    catch (Exception ex)
                    {
                        _logger?.LogWarning(ex, "Error during WebSocket closure for {Url}", _url);
                    }
                }
                _socket.Dispose();
                _socket = null;
                _cts?.Dispose();
                _cts = null;

                Connected = false;
            }
        }

        public void Dispose()
        {
            Disconnect().GetAwaiter().GetResult();
        }
    }
}
