using CrystalFinance.Api.Startup;
using CrystalFinanceLibrary.Logic;

var builder = WebApplication.CreateBuilder(args);

builder.AddDependencies();
builder.AddAuthentication();
builder.Services.AddScoped<TransactionImportService>();
var app = builder.Build();

app.UseOpenApi();

app.UseHttpsRedirection();

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

app.Run();
