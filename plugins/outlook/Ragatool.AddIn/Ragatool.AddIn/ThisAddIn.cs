using Microsoft.Extensions.Logging;
using Microsoft.Office.Core;
using Microsoft.VisualStudio.Tools.Applications.Runtime;
using Ragatool.AddIn.MessageHandlers;
using Ragatool.AddIn.Panes;
using Rumors.Desktop.Common.Commands;
using Rumors.Desktop.Common.Messages.MessageHub;
using Rumors.Desktop.Common.WebSocket;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Ragatool.AddIn
{
    public partial class ThisAddIn
    {
        public static WebSocketClient WebSocketClient { get; private set; }
        public static TaskPanes TaskPanes { get; set; }
        public static Ribbon Ribbon { get; private set; }
        public static SupportedCommands SupportedCommands { get; private set; } = new SupportedCommands();

       // private ILogger<ThisAddIn> _logger;
        private IMessageHub _messageHub;

        private void ThisAddIn_Startup(object sender, System.EventArgs e)
        {
            TaskPanes = new TaskPanes();
            _messageHub = MessageHub.Create(new WebSocketMessageSerializer())
                     .With(new PingMessageHandler())
                     .With(new CallCommandMessageHandler())
                     .With(new ErrorMessageHandler());
                     
            var wsUrl = "ws://localhost:8000/extensions/ws";
            var apiToken =
                System.Environment.GetEnvironmentVariable("RAGATOOL_TOKEN")
                ?? System.Environment.GetEnvironmentVariable("RAGATOUL_TOKEN");
            List<string> subProtocols = null;
            if (!string.IsNullOrWhiteSpace(apiToken))
            {
                subProtocols = new List<string> { "ragatool", apiToken.Trim() };
            }
            WebSocketClient = new WebSocketClient(wsUrl, subProtocols);
            WebSocketClient.OnMessage += async (webSocketMessage) =>
            {
                await _messageHub.Handle(webSocketMessage);
            };

            WebSocketClient.OnOpen += async () =>
            {

                var commands = SupportedCommands.CommandsAsJson(GetAccounts());
                var message = new WebSocketClientMessage
                {
                    Type = "ping",
                    Payload = commands
                };
            
                await WebSocketClient.Send(message.ToJsonString());
            };
        }

        private void ThisAddIn_Shutdown(object sender, System.EventArgs e)
        {
            // Note: Outlook no longer raises this event. If you have code that 
            //    must run when Outlook shuts down, see https://go.microsoft.com/fwlink/?LinkId=506785
        }

        #region VSTO generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InternalStartup()
        {
            this.Startup += new System.EventHandler(ThisAddIn_Startup);
            this.Shutdown += new System.EventHandler(ThisAddIn_Shutdown);
        }

        protected override IRibbonExtensibility CreateRibbonExtensibilityObject()
        {
            Ribbon = new Ribbon();
            return Ribbon;
        }

        #endregion

        private string GetAccounts()
        {
            var session = Globals.ThisAddIn.Application.Session;
            var accounts = session.Accounts;

            var result = new List<string>();
            foreach (Microsoft.Office.Interop.Outlook.Account account in accounts)
            {
                result.Add(account.DisplayName);
            }
            return string.Join(", ", result);
        }
    }
}
