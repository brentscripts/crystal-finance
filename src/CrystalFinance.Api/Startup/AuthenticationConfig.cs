using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Identity.Web;

namespace CrystalFinance.Api.Startup;

public static class AuthenticationConfig
{
    public static void AddAuthentication(this WebApplicationBuilder builder)
    {
        builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));

        builder.Services.AddAuthorization(options =>
        {
            options.AddPolicy("API.UserAccess", policy =>
            {
                policy.RequireScope("access_as_user");
            });
        });
    }
}
