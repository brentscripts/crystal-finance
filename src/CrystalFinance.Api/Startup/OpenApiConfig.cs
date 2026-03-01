using Scalar.AspNetCore;

namespace CrystalFinance.Api.Startup;

public static class OpenApiConfig
{
    public static void AddOpenApiServices(this IServiceCollection services)
    {
        services.AddOpenApi(options =>
        {
            options.AddDocumentTransformer<OpenApiTransformer>();
        });
    }


    public static void UseOpenApi(this WebApplication app)
    {
        if (app.Environment.IsDevelopment())
        {
            app.MapOpenApi();
            app.MapScalarApiReference("/scalar", options =>
            {
                options.Title = "The Crystal Finance API";
                options.Theme = ScalarTheme.Saturn;
                options.Layout = ScalarLayout.Modern;
                options.HideClientButton = true;

                options.AddPreferredSecuritySchemes("OAuth2") // This is the schemaKey from above
                .AddAuthorizationCodeFlow("OAuth2", flow =>
                {
                    // Entra ID v2.0 Endpoints
                    flow.AuthorizationUrl = app.Configuration["AzureAd:AuthorizationUrl"];
                    flow.TokenUrl = app.Configuration["AzureAd:TokenUrl"];
                    flow.ClientId = app.Configuration["AzureAd:ClientId"];
                    flow.SelectedScopes = [app.Configuration["AzureAd:Scopes"]!];
                    flow.RedirectUri = "https://localhost:7121/scalar/v1";
                });
            });
        }
    }
}
