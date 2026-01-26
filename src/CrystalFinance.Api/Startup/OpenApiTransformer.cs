using Microsoft.AspNetCore.OpenApi;

namespace CrystalFinance.Api.Startup;

// Acknowledgement: This code is based on an implementation by Hals.
// Source: "Setup Scalar with Microsoft.AspNetCore.OpenApi and OAuth2"
// Link: https://hals.app/blog/dotnet-openapi-scalar-oauth2/
public class OpenApiTransformer(IConfiguration configuration) : IOpenApiDocumentTransformer
{
    public Task TransformAsync(
        OpenApiDocument document,
        OpenApiDocumentTransformerContext context,
        CancellationToken cancellationToken
    )
    {
        document.Info = new OpenApiInfo
        {
            Title = "Echo AyelixProxyApi"
        };

        var authority = configuration["AzureAd:AuthorityUrl"]; // Learn more here https://learn.microsoft.com/en-us/entra/identity-platform/msal-client-application-configuration#authority
        var audience = configuration["AzureAd:ClientId"]; // In this example this is the guid Client Id of the Api
        var schemaKey = "OAuth2"; // This name is used as a key, and could be anything as long as you are consistent.
        var scopes = new Dictionary<string, string>
        {
            {
                configuration["AzureAd:Scopes"], // Actual Scope
                "API.UserAccess" // Human readable description
            },
        };
        var securitySchemes = new Dictionary<string, IOpenApiSecurityScheme>
        {
            [schemaKey] = new OpenApiSecurityScheme
            {
                Type = SecuritySchemeType.OAuth2,
                Scheme = "OAuth2",
                Flows = new OpenApiOAuthFlows
                {
                    AuthorizationCode = new OpenApiOAuthFlow
                    {
                        AuthorizationUrl = new Uri(configuration["AzureAd:AuthorizationUrl"]),
                        TokenUrl = new Uri(configuration["AzureAd:TokenUrl"]),
                        Scopes = scopes,
                    },
                },
            },
        };
        document.Components ??= new OpenApiComponents();
        document.Components.SecuritySchemes = securitySchemes;

        var securityRequirement = new OpenApiSecurityRequirement
        {
            [new OpenApiSecuritySchemeReference(schemaKey, document)] = [.. scopes.Keys],
        };

        document.Security = [securityRequirement];

        return Task.CompletedTask;
    }
}
