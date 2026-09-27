document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log("mcp.js loaded");


        const mcpEnabled =
            document.getElementById(
                "mcpEnabled"
            );

        const mcpModeStatus =
            document.getElementById(
                "mcpModeStatus"
            );

        const mcpTool =
            document.getElementById(
                "mcpTool"
            );

        const mcpArguments =
            document.getElementById(
                "mcpArguments"
            );

        const mcpResult =
            document.getElementById(
                "mcpResult"
            );

        const mcpServerStatusText =
            document.getElementById(
                "mcpServerStatusText"
            );

        const mcpServerStatusDot =
            document.getElementById(
                "mcpServerStatusDot"
            );

        const mcpToolGrid = 
            document.getElementById(
                "mcpToolGrid"
            );

        const mcpToolText = 
            document.getElementById(
                "mcpToolText"
            );


        console.log({
            mcpEnabled,
            mcpModeStatus,
            mcpTool,
            mcpArguments,
            mcpResult
        });


        const mcpExamples = {

            get_accommodations: {},

            get_accommodation_by_city: {
                city: "Sydney"
            },

            search_accommodations: {
                city: "Sydney",
                max_price: 400,
                guests: 2,
                type: "Hotel"
            },

            check_accommodation_availability: {
                accommodation_id: 2,
                check_in: "2026-10-05",
                check_out: "2026-10-08"
            },

            list_tripagent_services: {},

            get_service_status: {
                service_name:
                    "accommodation"
            },

            list_available_tools: {
                feature:
                    "accommodation"
            },

            get_tripagent_help: {
                topic: "mcp"
            },

            get_system_summary: {}
        };


        mcpEnabled.addEventListener(
            "change",
            function () {

                if (mcpEnabled.checked) {

                    mcpModeStatus.textContent = "ON";

                    mcpTool.disabled = false;

                    mcpArguments.disabled = false;

                    mcpServerStatusText.textContent = 
                        "Connected to MCP server";

                    mcpServerStatusDot.classList.remove(
                        "mcp-status-off"
                    );

                    mcpServerStatusDot.classList.add(
                        "mcp-status-on"
                    );

                    mcpToolGrid.style.display = "block";

                    mcpToolText.textContent = 
                        "MCP Mode is available with tools below:";


                } else {

                    mcpModeStatus.textContent = "OFF";

                    mcpTool.disabled = true;

                    mcpArguments.disabled = true;

                    mcpServerStatusText.textContent = 
                        "Disconnected to MCP server";

                    mcpServerStatusDot.classList.remove(
                        "mcp-status-on"
                    );
        
                    mcpServerStatusDot.classList.add(
                        "mcp-status-off"
                    );

                    mcpToolGrid.style.display = "none";

                    mcpToolText.textContent = 
                        "MCP Mode is disabled.";

                    mcpResult.textContent =
                        "MCP Mode is disabled.";
                }
            }
        );


        mcpTool.addEventListener(
            "change",
            function () {

                console.log(
                    "Selected MCP tool:",
                    mcpTool.value
                );

                const example =
                    mcpExamples[
                        mcpTool.value
                    ] || {};

                mcpArguments.value =
                    JSON.stringify(
                        example,
                        null,
                        2
                    );
            }
        );


        window.callMCPTool =
            async function () {

                if (!mcpEnabled.checked) {

                    mcpResult.textContent =
                        "MCP Mode is disabled.";

                    return;
                }


                const tool =
                    mcpTool.value;

                const argumentsText =
                    mcpArguments
                        .value
                        .trim();


                if (!tool) {

                    mcpResult.textContent =
                        "Please select a tool.";

                    return;
                }


                let argumentsData = {};

                try {

                    argumentsData =
                        argumentsText
                            ? JSON.parse(
                                argumentsText
                            )
                            : {};

                } catch (error) {

                    mcpResult.textContent =
                        "Arguments must be valid JSON.";

                    return;
                }


                mcpResult.textContent =
                    `Calling ${tool}...`;


                try {

                    const response =
                        await fetch(
                            `${API_URL}/mcp/call`,
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json",
                                    "X-MCP-Mode":
                                        mcpEnabled.checked ? "on" : "off"
                                },

                                body:
                                    JSON.stringify({
                                        tool:
                                            tool,
                                        arguments:
                                            argumentsData
                                    })
                            }
                        );


                    const data =
                        await response.json();


                    mcpResult.textContent =
                        JSON.stringify(
                            data,
                            null,
                            2
                        );


                } catch (error) {

                    console.error(
                        error
                    );

                    mcpResult.textContent =
                        "Unable to connect to MCP service.";
                }
            };
    }
);