using CrystalFinanceLibrary.Logic;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Identity.Web;

namespace CrystalFinance.Api.Startup;

public static class DependenciesConfig
{
    public static void AddDependencies(this WebApplicationBuilder builder)
    {
        builder.Services.AddControllers();

        builder.Services.AddOpenApiServices();

        builder.Services.AddAuthorization();       
    }
}
