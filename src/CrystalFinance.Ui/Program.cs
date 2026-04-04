using CrystalFinance.Ui;
using CrystalFinance.Ui.Models;
using CrystalFinance.Ui.Services;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Authentication;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using MudBlazor.Services;



var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

builder.Services.AddMudServices();

builder.Services.AddScoped(sp => 
{
    var authorizationMessageHandler = sp.GetRequiredService<AuthorizationMessageHandler>();
    authorizationMessageHandler.InnerHandler = new HttpClientHandler();
    var downstreamApiBaseUrl = builder.Configuration["DownstreamApi:BaseUrl"];
    // Fix CS8620: Ensure authorizedUrls is non-nullable and contains no nulls
    var authorizedUrls = new[] { downstreamApiBaseUrl! };
    // Fix CS8620: Ensure scopes is a non-nullable IEnumerable<string>
    var downstreamApiScopes = builder.Configuration.GetSection("DownstreamApi:Scopes").Get<string[]>()?.Where(s => !string.IsNullOrWhiteSpace(s)).Select(s => s.Trim()).ToArray() ?? Array.Empty<string>();
    authorizationMessageHandler = authorizationMessageHandler.ConfigureHandler(
        authorizedUrls: authorizedUrls,
        scopes: downstreamApiScopes);
    return new HttpClient(authorizationMessageHandler)
    {
        BaseAddress = new Uri(downstreamApiBaseUrl ?? string.Empty)
    };
});

builder.Services.AddMsalAuthentication<RemoteAuthenticationState,CustomUserAccount>(options =>
{
    builder.Configuration.Bind("AzureAd", options.ProviderOptions.Authentication);

    // Load scopes from configuration
    var scopes = builder.Configuration.GetSection("AzureAd:Scopes").Get<string[]>();
    if (scopes != null)
    {
        foreach (var scope in scopes.Where(s => !string.IsNullOrWhiteSpace(s)))
        {
            options.ProviderOptions.DefaultAccessTokenScopes.Add(scope.Trim());
            options.UserOptions.RoleClaim = "appRole"; // Map Entra ID roles to "appRole" claim
        }
    }
}).AddAccountClaimsPrincipalFactory<RemoteAuthenticationState,CustomUserAccount,CustomAccountFactory>();

builder.Services.AddHttpClient<TransactionProcessingService>(client =>
{
    client.BaseAddress = new Uri(builder.Configuration["CrystalFinanceApi:BaseUrl"] ?? string.Empty);
}).AddHttpMessageHandler(sp =>
{
    // Get a fresh handler from DI
    var handler = sp.GetRequiredService<AuthorizationMessageHandler>();

    // Configure it specifically for your Finance API
    var apiBaseUrl = builder.Configuration["CrystalFinanceApi:BaseUrl"] ?? string.Empty;
    var apiScopes = builder.Configuration.GetSection("DownstreamApi:Scopes").Get<string[]>() ?? Array.Empty<string>();

    return handler.ConfigureHandler(
        authorizedUrls: new[] { apiBaseUrl },
        scopes: apiScopes
    );
});

//builder.Services.AddHttpClient<FinanceCrudService>();

await builder.Build().RunAsync();
