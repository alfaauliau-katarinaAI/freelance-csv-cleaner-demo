const assert = require('node:assert/strict');
const {calculate} = require('./calc.js');
function close(a,b){assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`)}
let a=calculate({portions:10,packaging:1000,overhead:2000,margin:50,ingredients:[{name:'kopi',packPrice:100000,packQty:1000,usage:100,waste:10}]});
close(a.ingredientCost,11000);close(a.total,23000);close(a.hpp,2300);close(a.rawPrice,4600);close(a.recommendedPrice,5000);close(a.profit,2700);close(a.realizedMargin,54);
a=calculate({portions:0,packaging:-1,overhead:-50,margin:150,ingredients:[{name:'a',packPrice:100,packQty:0,usage:20,waste:0}]});
close(a.hpp,0);assert.equal(a.portions,1);assert.equal(a.margin,99);assert.equal(a.valid,false);assert.ok(a.warnings.some(w=>w.includes('isi kemasan')));
a=calculate({portions:2,packaging:0,overhead:0,margin:0,ingredients:[{name:'a',packPrice:2000,packQty:2,usage:1,waste:100}]});
close(a.hpp,1000);close(a.recommendedPrice,1000);assert.equal(a.valid,true);
a=calculate({portions:1,packaging:0,overhead:0,margin:30,ingredients:[{name:'A',packPrice:1000,packQty:0,usage:1,waste:0}]});assert.equal(a.valid,false);assert.ok(a.warnings.length>0);
a=calculate({portions:1,packaging:0,overhead:0,margin:0,ingredients:[{name:'A',packPrice:1000,packQty:1000,usage:1,waste:101}]});assert.equal(a.valid,false);
console.log('PASS: 5 calculation test scenarios');
