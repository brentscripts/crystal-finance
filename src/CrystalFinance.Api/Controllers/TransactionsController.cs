using CrystalFinanceLibrary.Logic;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CrystalFinance.Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [Authorize(Policy = "API.UserAccess")]
    public class TransactionsController : ControllerBase
    {
        private readonly TransactionImportService _importService;

        public TransactionsController(TransactionImportService importService)
        {
            _importService = importService;
        }

        [HttpPost("import")]
        public async Task<IActionResult> ImportTransactions(IFormFile file, [FromQuery] string source)
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest("No file uploaded.");
            }
            using var stream = file.OpenReadStream();
            var records = await _importService.ImportTransactions(stream, source).ToListAsync();
            return Ok(records);
        }
    }
}
