export function useContracts(){return{contracts:[],total:0,isLoading:false}}
export function useContract(){return{data:null,isLoading:false}}
export function useUploadContract(){return{mutateAsync:async()=>{},isPending:false,progress:0}}
